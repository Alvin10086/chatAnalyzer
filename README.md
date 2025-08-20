# chatAnalyzer

This is a project aimed in analyze the chat based on the space, time sent, sender, tone, and keywords to detect the crime happen or not. The crime focused here was the drug trafficating. The drug keywords was setted in malay, english, chinese. The emoji was also analyzed. 
The fyp.ipndb was the file used to testing and it has previous version using scispacy and also the malaya to analyze the chat.
The chatAnalyzer.py was the file implemented, it can support for whatsapp and facebook. 
To use the chatAnalyzer.py, you need to install some package:
pip install pandas matplotlib seaborn pyqt5
run the command to install the packages.
Then, in the environment you install the package, run the file directly or run
python chat_analyzer.py
to run the code. 

The whatsapp_drug_chats can be used as the sample data.
The result will be stored in whatsapp_chats_scored.csv
