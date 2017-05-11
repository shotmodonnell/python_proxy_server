Readme for python proxy by Mark O'Donnell:

Overview:
	A simple web proxy built using python which can be configured to ban
	certain websites through a management console and which can make web
	browsing more efficient through caching of whole webpages.

To begin:
	Open a command window in the OS of your choice (with python installed)
	and navigate to the appropriate directory. Enter the command:
	"python proxyCache.py <port>"
	where <port> is replaced with the port number you would like to use.
	
Running:
	Once the above is done a GUI will open with a list of banned websites
	which can be added to through the GUI. Also the console will begin to
	display activity.
	Configure your browser of choice to use localhost and your specified 
	port as its proxy and you can begin to use it.

Troubleshooting:
	If any errors are experienced the DEBUG  variable in the source code can
	be changed to 1. This will output more data to the console about what is
	happening during the course of the program.