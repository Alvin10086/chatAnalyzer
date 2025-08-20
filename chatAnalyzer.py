import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
import seaborn as sns
import re
from datetime import datetime
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                             QPushButton, QLabel, QFileDialog, QComboBox, QTabWidget, 
                             QTextEdit, QTableWidget, QTableWidgetItem, QSplitter, 
                             QHeaderView, QMessageBox, QProgressBar, QGroupBox)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QFont, QColor

# Simulated scoring functions
def score_message(message):
    """Score message based on drug-related keywords and patterns"""
    if not isinstance(message, str):
        return 0
        
    score = 0
    message_lower = message.lower()
    
    # Drug-related keywords
    drug_keywords = [
        'weed', 'marijuana', 'cocaine', 'heroin', 'ecstasy', 'mdma', 'lsd', 'acid',
        'speed', 'meth', 'crystal', 'amphetamine', 'opioid', 'oxy', 'xanax', 'valium',
        'prescription', 'pills', 'dealer', 'score', 'hook up', 'bag', 'ounce', 'gram',
        '8ball', 'pot', 'dope', 'smoke', 'joint', 'blunt', 'bong', 'pipe'
    ]
    
    # Check for drug-related keywords
    for keyword in drug_keywords:
        if keyword in message_lower:
            score += 5
    
    # Check for common patterns
    patterns = [
        (r'\$\d+', 3),  # Money references
        (r'\b\d+\s*(g|mg|oz|gram|ounce)\b', 4),  # Quantity references
        (r'\bmeet\b.*\b(later|tonight|tomorrow)\b', 3),  # Meeting arrangements
        (r'\b(text|call|pm|dm)\b', 2),  # Private communication
    ]
    
    for pattern, pattern_score in patterns:
        if re.search(pattern, message_lower):
            score += pattern_score
            
    return min(score, 10)  # Cap at 10

def is_drug(message):
    """Determine if message is likely drug-related"""
    return score_message(message) >= 5

def detect_transaction(text):
    """Detect potential transactions in text"""
    transaction_indicators = [
        r'\$\d+', r'\d+\s*(dollars|bucks)', r'pay\s*(you|me)', r'venmo', r'cash\s*app',
        r'zelle', r'wire\s*transfer', r'bitcoin', r'crypto', r'payment', r'send\s*money'
    ]
    
    text_lower = text.lower()
    for pattern in transaction_indicators:
        if re.search(pattern, text_lower):
            return True
    return False

def detect_location(text):
    """Detect potential locations in text"""
    location_indicators = [
        r'\b(at|in|to|from|near)\s+[A-Z][a-z]+', r'\b(street|ave|avenue|road|rd|boulevard|blvd)\b',
        r'\b(park|mall|plaza|center|store|shop)\b', r'\d+\s*(miles|blocks|minutes)\b'
    ]
    
    text_lower = text.lower()
    for pattern in location_indicators:
        if re.search(pattern, text_lower):
            return True
    return False

def detect_personal_info(text):
    """Detect potential personal information in text"""
    personal_info_indicators = [
        r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # Phone numbers
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',  # Email addresses
        r'\b\d{4}\s?\d{4}\s?\d{4}\s?\d{4}\b',  # Credit card numbers
        r'\b\d{3}-\d{2}-\d{4}\b',  # SSN
        r'\b(birth|born|age|dob)\b.*\b(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})\b'  # Birth dates
    ]
    
    text_lower = text.lower()
    for pattern in personal_info_indicators:
        if re.search(pattern, text_lower):
            return True
    return False

class ChatAnalyzerApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WhatsApp & Facebook Chat Analyzer")
        self.setGeometry(100, 100, 1200, 800)
        
        # Initialize data
        self.df = None
        self.results_df = None
        self.current_file = None
        
        # Set up UI
        self.setup_ui()
        
    def setup_ui(self):
        # Central widget and main layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Top panel with controls
        top_panel = QGroupBox("File Information")
        top_layout = QVBoxLayout(top_panel)
        
        # File info section
        file_info_layout = QHBoxLayout()
        self.file_label = QLabel("No file loaded")
        file_info_layout.addWidget(self.file_label)
        file_info_layout.addStretch()
        
        self.load_btn = QPushButton("Load Chat File")
        self.load_btn.clicked.connect(self.load_file)
        file_info_layout.addWidget(self.load_btn)
        
        top_layout.addLayout(file_info_layout)
        
        # Platform selection
        platform_layout = QHBoxLayout()
        platform_layout.addWidget(QLabel("Platform:"))
        
        self.platform_combo = QComboBox()
        self.platform_combo.addItems(["Auto Detect", "WhatsApp", "Facebook"])
        platform_layout.addWidget(self.platform_combo)
        
        self.analyze_btn = QPushButton("Analyze")
        self.analyze_btn.clicked.connect(self.analyze_data)
        self.analyze_btn.setEnabled(False)
        platform_layout.addWidget(self.analyze_btn)
        
        platform_layout.addStretch()
        top_layout.addLayout(platform_layout)
        
        main_layout.addWidget(top_panel)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        main_layout.addWidget(self.progress_bar)
        
        # Tab widget for different views
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)
        
        # Overview tab
        self.overview_tab = QWidget()
        self.overview_layout = QVBoxLayout(self.overview_tab)
        self.tabs.addTab(self.overview_tab, "Overview")
        
        # Sender analysis tab
        self.sender_tab = QWidget()
        self.sender_layout = QVBoxLayout(self.sender_tab)
        self.tabs.addTab(self.sender_tab, "Sender Analysis")
        
        # Raw data tab
        self.raw_tab = QWidget()
        self.raw_layout = QVBoxLayout(self.raw_tab)
        self.tabs.addTab(self.raw_tab, "Raw Data")
        
        # Status bar
        self.statusBar().showMessage("Ready to load chat data")
        
    def load_file(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Open Chat File", "", "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            self.current_file = file_path
            self.file_label.setText(f"Loaded: {file_path.split('/')[-1]}")
            
            try:
                self.df = pd.read_csv(file_path, encoding='ISO-8859-1')
                self.statusBar().showMessage(f"Loaded {len(self.df)} messages from {file_path}")
                self.analyze_btn.setEnabled(True)
                
                # Show a preview of the data
                self.show_data_preview()
                
            except Exception as e:
                QMessageBox.critical(self, "Error", f"Failed to load file: {str(e)}")
    
    def show_data_preview(self):
        # Clear previous content
        for i in reversed(range(self.overview_layout.count())): 
            widget = self.overview_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Create preview group
        preview_group = QGroupBox("Data Preview")
        preview_layout = QVBoxLayout(preview_group)
        
        # Show column information
        cols_text = f"<b>Columns detected:</b> {', '.join(self.df.columns)}"
        cols_label = QLabel(cols_text)
        preview_layout.addWidget(cols_label)
        
        # Show first few rows
        preview_table = QTableWidget()
        preview_table.setRowCount(min(5, len(self.df)))
        preview_table.setColumnCount(min(5, len(self.df.columns)))
        preview_table.setHorizontalHeaderLabels(self.df.columns[:5])
        
        for row_idx in range(min(5, len(self.df))):
            for col_idx in range(min(5, len(self.df.columns))):
                item = QTableWidgetItem(str(self.df.iloc[row_idx, col_idx]))
                preview_table.setItem(row_idx, col_idx, item)
        
        preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        preview_layout.addWidget(preview_table)
        
        self.overview_layout.addWidget(preview_group)
    
    def analyze_data(self):
        if self.df is None:
            return
            
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        # Process in a separate thread would be better, but for simplicity we'll do it here
        try:
            # Detect platform if auto-selected
            platform = self.detect_platform()
            
            # Standardize column names based on platform
            self.standardize_columns(platform)
            
            # Apply scoring
            self.results_df = self.df.copy()
            self.results_df['suspicion_score'] = self.results_df['message'].astype(str).apply(score_message)
            self.results_df['is_suspicious'] = self.results_df['suspicion_score'] >= 5
            self.results_df['has_transaction'] = self.results_df['message'].astype(str).apply(detect_transaction)
            self.results_df['has_location'] = self.results_df['message'].astype(str).apply(detect_location)
            self.results_df['has_personal_info'] = self.results_df['message'].astype(str).apply(detect_personal_info)
            
            # Update UI with results
            self.update_overview_tab()
            self.update_sender_tab()
            self.update_raw_tab()
            
            self.statusBar().showMessage(f"Analysis complete. Found {self.results_df['is_suspicious'].sum()} suspicious messages.")
            
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Analysis failed: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
    
    def detect_platform(self):
        if self.platform_combo.currentText() != "Auto Detect":
            return self.platform_combo.currentText()
            
        # Auto-detect platform based on column names
        columns = set(self.df.columns.str.lower())
        
        # Check for WhatsApp-specific columns
        whatsapp_indicators = {'from', 'to', 'time (utc)', 'time (local)', 'message'}
        if whatsapp_indicators.issubset(columns):
            return "WhatsApp"
            
        # Check for Facebook-specific columns
        facebook_indicators = {'sender_name', 'timestamp_ms', 'content'}
        if facebook_indicators.issubset(columns):
            return "Facebook"
            
        # Check for partial matches
        if 'from' in columns and 'message' in columns:
            return "WhatsApp"
        elif 'sender_name' in columns and 'content' in columns:
            return "Facebook"
                
        return "Unknown"
    
    def standardize_columns(self, platform):
        # Standardize column names for easier processing
        column_map = {}
        
        if platform == "WhatsApp":
            # Map WhatsApp columns to standard names
            if 'from' in self.df.columns:
                column_map['From'] = 'sender'
            if 'to' in self.df.columns:
                column_map['To'] = 'receiver'
            if 'message' in self.df.columns:
                column_map['Message'] = 'message'
            elif 'content' in self.df.columns:
                column_map['Content'] = 'message'
                
            # Handle timestamp columns
            if 'time (local)' in self.df.columns:
                column_map['Time (local)'] = 'timestamp'
            elif 'timestamp' in self.df.columns:
                column_map['Timestamp'] = 'timestamp'
            elif 'date' in self.df.columns:
                column_map['Date'] = 'timestamp'
                
        elif platform == "Facebook":
            # Map Facebook columns to standard names
            if 'sender_name' in self.df.columns:
                column_map['sender_name'] = 'sender'
            if 'content' in self.df.columns:
                column_map['content'] = 'message'
            elif 'message' in self.df.columns:
                column_map['message'] = 'message'
                
            # Handle timestamp columns
            if 'timestamp_ms' in self.df.columns:
                # Convert Facebook timestamp (ms) to datetime
                self.df['timestamp'] = pd.to_datetime(self.df['timestamp_ms'], unit='ms')
                # Don't need to map this as we're creating a new column
            elif 'timestamp' in self.df.columns:
                column_map['timestamp'] = 'timestamp'
            elif 'date' in self.df.columns:
                column_map['date'] = 'timestamp'
        
        # Rename columns
        self.df.rename(columns=column_map, inplace=True)
        
        # Ensure we have required columns
        required = ['sender', 'message']
        for col in required:
            if col not in self.df.columns:
                raise ValueError(f"Required column '{col}' not found in data")
        
        # Convert timestamp to datetime if it exists
        if 'timestamp' in self.df.columns:
            self.df['timestamp'] = pd.to_datetime(self.df['timestamp'], errors='coerce')
    
    def update_overview_tab(self):
        # Clear previous content
        for i in reversed(range(self.overview_layout.count())): 
            widget = self.overview_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Create summary stats
        total_msgs = len(self.results_df)
        suspicious_msgs = self.results_df['is_suspicious'].sum()
        transaction_msgs = self.results_df['has_transaction'].sum()
        location_msgs = self.results_df['has_location'].sum()
        personal_info_msgs = self.results_df['has_personal_info'].sum()
        
        stats_text = f"""
        <h3>Analysis Summary</h3>
        <b>Total Messages:</b> {total_msgs}<br>
        <b>Suspicious Messages:</b> {suspicious_msgs} ({suspicious_msgs/total_msgs*100:.1f}%)<br>
        <b>Potential Transactions:</b> {transaction_msgs}<br>
        <b>Location Mentions:</b> {location_msgs}<br>
        <b>Personal Info Detected:</b> {personal_info_msgs}<br>
        """
        
        stats_label = QLabel(stats_text)
        self.overview_layout.addWidget(stats_label)
        
        # Create matplotlib figures
        fig1 = self.create_suspicion_distribution_plot()
        fig2 = self.create_sender_analysis_plot()
        fig3 = self.create_timeline_plot()
        
        # Add plots to layout
        self.overview_layout.addWidget(FigureCanvas(fig1))
        self.overview_layout.addWidget(FigureCanvas(fig2))
        self.overview_layout.addWidget(FigureCanvas(fig3))
    
    def create_suspicion_distribution_plot(self):
        fig, ax = plt.subplots(figsize=(10, 4))
        sns.histplot(data=self.results_df, x='suspicion_score', bins=10, ax=ax)
        ax.set_title('Distribution of Suspicion Scores')
        ax.set_xlabel('Suspicion Score')
        ax.set_ylabel('Count')
        plt.tight_layout()
        return fig
    
    def create_sender_analysis_plot(self):
        # Group by sender and calculate metrics
        sender_stats = self.results_df.groupby('sender').agg({
            'suspicion_score': 'mean',
            'is_suspicious': 'sum',
            'has_transaction': 'sum',
            'has_location': 'sum',
            'has_personal_info': 'sum'
        }).sort_values('suspicion_score', ascending=False)
        
        fig, ax = plt.subplots(figsize=(10, 6))
        x = range(len(sender_stats))
        width = 0.15
        
        ax.bar(x, sender_stats['is_suspicious'], width, label='Suspicious')
        ax.bar([i + width for i in x], sender_stats['has_transaction'], width, label='Transactions')
        ax.bar([i + width*2 for i in x], sender_stats['has_location'], width, label='Locations')
        ax.bar([i + width*3 for i in x], sender_stats['has_personal_info'], width, label='Personal Info')
        
        ax.set_xlabel('Sender')
        ax.set_ylabel('Count')
        ax.set_title('Message Analysis by Sender')
        ax.set_xticks([i + width*1.5 for i in x])
        ax.set_xticklabels(sender_stats.index, rotation=45, ha='right')
        ax.legend()
        
        plt.tight_layout()
        return fig
    
    def create_timeline_plot(self):
        # Try to create a timeline if we have timestamp data
        if 'timestamp' in self.results_df.columns:
            try:
                # Convert to datetime if not already
                time_df = self.results_df.copy()
                time_df['timestamp'] = pd.to_datetime(time_df['timestamp'], errors='coerce')
                time_df = time_df.dropna(subset=['timestamp'])
                
                # Group by date
                time_df['date'] = time_df['timestamp'].dt.date
                daily_counts = time_df.groupby('date').size()
                daily_suspicious = time_df[time_df['is_suspicious']].groupby('date').size()
                
                fig, ax = plt.subplots(figsize=(10, 4))
                ax.plot(daily_counts.index, daily_counts.values, label='All Messages', alpha=0.7)
                ax.scatter(daily_suspicious.index, daily_suspicious.values, 
                          color='red', label='Suspicious Messages', alpha=0.8)
                ax.set_title('Message Activity Over Time')
                ax.set_xlabel('Date')
                ax.set_ylabel('Message Count')
                ax.legend()
                plt.xticks(rotation=45)
                plt.tight_layout()
                return fig
            except Exception as e:
                print(f"Timeline error: {e}")
                pass
                
        # Fallback if timeline can't be created
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, 'Timeline data not available', 
                horizontalalignment='center', verticalalignment='center',
                transform=ax.transAxes, fontsize=14)
        ax.set_title('Message Activity Over Time')
        return fig
    
    def update_sender_tab(self):
        # Clear previous content
        for i in reversed(range(self.sender_layout.count())): 
            widget = self.sender_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Create sender selector
        sender_layout = QHBoxLayout()
        sender_layout.addWidget(QLabel("Select Sender:"))
        
        sender_combo = QComboBox()
        senders = self.results_df['sender'].unique()
        sender_combo.addItems(senders)
        sender_combo.currentTextChanged.connect(self.update_sender_details)
        sender_layout.addWidget(sender_combo)
        
        sender_layout.addStretch()
        self.sender_layout.addLayout(sender_layout)
        
        # Add splitter for details and messages
        splitter = QSplitter(Qt.Vertical)
        self.sender_layout.addWidget(splitter)
        
        # Sender details area
        self.sender_details = QTextEdit()
        self.sender_details.setReadOnly(True)
        splitter.addWidget(self.sender_details)
        
        # Sender messages table
        self.sender_table = QTableWidget()
        splitter.addWidget(self.sender_table)
        
        # Set initial sender
        if len(senders) > 0:
            self.update_sender_details(senders[0])
    
    def update_sender_details(self, sender):
        if self.results_df is None:
            return
            
        # Filter data for selected sender
        sender_data = self.results_df[self.results_df['sender'] == sender]
        
        # Calculate stats
        total_msgs = len(sender_data)
        suspicious_msgs = sender_data['is_suspicious'].sum()
        avg_score = sender_data['suspicion_score'].mean()
        transaction_msgs = sender_data['has_transaction'].sum()
        location_msgs = sender_data['has_location'].sum()
        personal_info_msgs = sender_data['has_personal_info'].sum()
        
        # Update details text
        details_text = f"""
        <h3>Analysis for {sender}</h3>
        <b>Total Messages:</b> {total_msgs}<br>
        <b>Suspicious Messages:</b> {suspicious_msgs} ({suspicious_msgs/total_msgs*100:.1f}%)<br>
        <b>Average Suspicion Score:</b> {avg_score:.2f}<br>
        <b>Potential Transactions:</b> {transaction_msgs}<br>
        <b>Location Mentions:</b> {location_msgs}<br>
        <b>Personal Info Detected:</b> {personal_info_msgs}<br>
        """
        
        self.sender_details.setHtml(details_text)
        
        # Update messages table
        self.update_sender_table(sender_data)
    
    def update_sender_table(self, sender_data):
        # Prepare table data
        table_data = sender_data[['timestamp', 'message', 'suspicion_score', 
                                 'has_transaction', 'has_location', 'has_personal_info']].copy()
        table_data = table_data.sort_values('suspicion_score', ascending=False)
        
        # Configure table
        self.sender_table.setRowCount(len(table_data))
        self.sender_table.setColumnCount(6)
        self.sender_table.setHorizontalHeaderLabels([
            'Timestamp', 'Message', 'Score', 'Transaction', 'Location', 'Personal Info'
        ])
        
        # Populate table
        for row_idx, (_, row) in enumerate(table_data.iterrows()):
            # Timestamp
            timestamp_item = QTableWidgetItem(str(row['timestamp']))
            self.sender_table.setItem(row_idx, 0, timestamp_item)
            
            # Message
            message_item = QTableWidgetItem(str(row['message']))
            self.sender_table.setItem(row_idx, 1, message_item)
            
            # Score
            score_item = QTableWidgetItem(str(row['suspicion_score']))
            self.sender_table.setItem(row_idx, 2, score_item)
            
            # Transaction flag
            transaction_item = QTableWidgetItem("Yes" if row['has_transaction'] else "No")
            if row['has_transaction']:
                transaction_item.setBackground(QColor(255, 200, 200))  # Light red
            self.sender_table.setItem(row_idx, 3, transaction_item)
            
            # Location flag
            location_item = QTableWidgetItem("Yes" if row['has_location'] else "No")
            if row['has_location']:
                location_item.setBackground(QColor(200, 255, 200))  # Light green
            self.sender_table.setItem(row_idx, 4, location_item)
            
            # Personal info flag
            personal_item = QTableWidgetItem("Yes" if row['has_personal_info'] else "No")
            if row['has_personal_info']:
                personal_item.setBackground(QColor(255, 255, 200))  # Light yellow
            self.sender_table.setItem(row_idx, 5, personal_item)
        
        # Resize columns to content
        self.sender_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        
    def update_raw_tab(self):
        # Clear previous content
        for i in reversed(range(self.raw_layout.count())): 
            widget = self.raw_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        
        # Create raw data table
        raw_table = QTableWidget()
        self.raw_layout.addWidget(raw_table)
        
        # Configure table
        raw_table.setRowCount(min(1000, len(self.results_df)))  # Limit for performance
        raw_table.setColumnCount(len(self.results_df.columns))
        raw_table.setHorizontalHeaderLabels(self.results_df.columns)
        
        # Populate table
        for row_idx in range(min(1000, len(self.results_df))):
            row = self.results_df.iloc[row_idx]
            for col_idx, col_name in enumerate(self.results_df.columns):
                item = QTableWidgetItem(str(row[col_name]))
                
                # Highlight suspicious messages
                if col_name == 'is_suspicious' and row[col_name]:
                    item.setBackground(QColor(255, 200, 200))  # Light red
                
                raw_table.setItem(row_idx, col_idx, item)
        
        # Resize columns to content
        raw_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ChatAnalyzerApp()
    window.show()
    sys.exit(app.exec_())