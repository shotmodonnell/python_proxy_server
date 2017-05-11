import os,sys,thread,socket,select,Tkinter,collections

#constants

BACKLOG = 50
MAX_CACHE_SIZE = 10
MAX_DATA_RECV = 8192
DEBUG = 0
TIMEOUT = 2
BANLIST = ['www.boards.ie', 'boards.ie']
BANPAGE = 'HTTP/1.1 200 OK\n Content-Type: text/html \n <!DOCTYPE HTML PUBLIC '+"-//W3C//DTD HTML 4.01//EN"+"http://www.w3.org/TR/html4/strict.dtd"+'> \n <HTML><HEAD><TITLE>Bad Request</TITLE>\n<META HTTP-EQUIV="Content-Type" Content="text/html; charset=us-ascii"></HEAD>\n<BODY><h2>Bad Request</h2>\n<hr><p>Proxy Error. You have attempted to access a banned website. Stop that.</p>\n</BODY></HTML>\n'

#cache class
class cache():

	data = []
	requests = []
		
	def add(self, _data, _request):
		self.data.append(_data)
		self.requests.append(_request)
		if len(self.data) > MAX_CACHE_SIZE:
			self.data.pop(0)
			self.requests.pop(0)
		if(DEBUG):
			print "This begins the request added: "
			print self.requests[0]
			print "Here it ends and the data begins: "
			print self.data[0]
			print "There the data ends"
			
	def find(self, _request):
		try:
			position = self.requests.index(_request)
		except ValueError:
			return -1		
		return position
		
	def giveData(self, index):
		return self.data[index]
				

#GUI class
class simpleapp_tk(Tkinter.Tk):
    def __init__(self,parent):
        Tkinter.Tk.__init__(self,parent)
        self.parent = parent
        self.initialize()

    def initialize(self):
        self.grid()
        
        self.entry = Tkinter.Entry(self)
        self.entry.grid(column=0,row=0,sticky='EW')
        self.entry.bind("<Return>", self.OnPressEnter)

        button = Tkinter.Button(self,text=u"Add to banlist",command=self.OnButtonClick)
        button.grid(column=1,row=0)

        label = Tkinter.Label(self,anchor="w",fg="white",bg="blue")
        label.grid(column=0,row=1,columnspan=2,sticky='EW')
        
        self.banDisplay = Tkinter.Text(self)
        self.banDisplay.grid(column=0, row=2, columnspan=4, sticky='EW')
        
        self.banDisplay.insert(Tkinter.INSERT, "This is the list of banned websites \n")
        
        for x in range(0, len(BANLIST)):
        	self.banDisplay.insert(Tkinter.END, BANLIST[x]) 
        	self.banDisplay.insert(Tkinter.END, "\n")

        self.grid_columnconfigure(0,weight=1)
        self.resizable(True,True)

    def OnButtonClick(self):
    	newEntry = self.entry.get()
        BANLIST.append(newEntry)
        self.banDisplay.insert(Tkinter.END, newEntry)
        self.banDisplay.insert(Tkinter.END, "\n")

    def OnPressEnter(self,event):
    	newEntry = self.entry.get()
        BANLIST.append(newEntry)
        self.banDisplay.insert(Tkinter.END, newEntry)
        self.banDisplay.insert(Tkinter.END, "\n")



#Global Variables
cachedData = cache()

#proxy bits and bobs here
def proxy_thread(conn, client_addr):

	request = conn.recv(MAX_DATA_RECV)
	
	if len(request) > 4: #prevent invalid odd requests
		if (DEBUG):
			print "request: ", request 
		
		#parse the first line
		first_line = request.split(('\n')[0]) #This actually splits the request into a list separated by new line char
		print "first line: ", first_line[0] #First line[0] is the first line
		
		#get url
		url = first_line[0].split((' ')[0]) #Similar to above this actually splits the first line into a list separated by spaces
		try:
			protocol = url[2] #attempt to take proper info out of the line, the HTTP protocol
			requestType = url[0] #GET, CONNECT etc
			url = url[1] #The url itself
		except IndexError:
			print "List error for URL"

		#find the server and port		
		try:
			 http_pos = url.find("://") #find where the address starts
		except AttributeError:
			http_pos = url[0].find("://")
		if(http_pos == -1):
			temp = url #if there is no :// then there is no www and the url is this
		else:
			temp = url[(http_pos+3):] #takes from that position till end
			
		try:
			port_pos = temp.find(":") #find port if it is specified
		except AttributeError:
			port_pos = temp[0].find(":")
		
		try:
			webserver_pos = temp.find("/") #get the server and not the full URL here
		except AttributeError:
			webserver_pos = temp[0].find("/")
		if (webserver_pos == -1):
			webserver_pos = len(temp)
			
		webserver = ""
		port = -1
		if(port_pos==-1 or webserver_pos < port_pos): #default port
			port = 80
			webserver = temp[:webserver_pos]
		else: #when we know
			port = int((temp[(port_pos+1):])[:webserver_pos-port_pos-1])
			webserver = temp[:port_pos]
			
		if webserver in BANLIST: #check if server is allowed
			conn.send("That website is banned, how dare you. \n")
			conn.send('BANPAGE')
		else:			
			print "Connect to:", webserver, port
			
			if(cachedData.find(first_line[0]) != -1):
				conn.send(cachedData.giveData(cachedData.find(request)))
				if(DEBUG):
					print "Data taken from cache"
					print cachedData.giveData(cachedData.find(request))
					print "That was the data"
			else:	
				try:
					(soc_family, _, _, _, address) = socket.getaddrinfo(webserver,port)[0] #Grab the socket info
					s = socket.socket(soc_family) #Create an appropriate socket
					try: 
						s.connect(address)
					except TypeError:
						print  "Invalid webserver\port"
						
					#special usage for Connect requests:
					if requestType == 'CONNECT':				
						conn.send(protocol+' 200 Connection established \n'+'Proxy-agent %s\n\n Mark Proxy')
					else:
						s.send('%s %s %s\n'%(requestType, url, protocol) + '')
						
					socs = [conn, s] #Make a list for easier use later with select
					count = 0 #Count to Timeouts
					s.send(request)
					
					while 1:
						count += 1
						(recv, _, error) = select.select(socs, [], socs, 3) #Use select to efficiently handle inputs and outputs
						if error:
							break
						if recv:
							for in_ in recv:
								data = in_.recv(MAX_DATA_RECV)
								if in_ is conn:
									out = s #choose correct destination
								else:
									out = conn
								if data:
									out.send(data)
									cachedData.add(data, first_line[0]) #cache the data and the corresponding request
									count = 0
						if count == TIMEOUT:
							print "Timeout"
							break
						
				except socket.error, (value,message):
					if s:
						print "Error, closing socket"
						s.close()
					if conn:
						print "Error, closing connection"
						conn.close()
					print "Runtime error:",message,value
					sys.exit(1)	
			
	try:
		conn.close()
	except socket.error, (value,message):
		print "Conn error"
	try:
		s.close()
	except socket.error, (value, message):
		print "S error"
	except UnboundLocalError:
		print "No need to close S, S never opened"
		

#program
def actual_main(host, port):
	
	try:
		#create a socket
		s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		
		s.bind((host,port))
		
		#listening
		s.listen(BACKLOG) 
		
	except socket.error, (value, message):
		if s:
			s.close()
		print "could not open socket",message
		sys.exit(1)

	print "Listening"
			
	#get connection
	while 1:
		thread.start_new_thread(proxy_thread, s.accept())		
	s.close()
	

#GUI thread (must be main to play nice with TKinter
def main():
	
	#check the length of the command
	if(len(sys.argv) < 2):
		print "usage: proxy <port>"
		return sys.stdout
		
	#host and port infor
	host = ''
	port = int(sys.argv[1])
	
	thread.start_new_thread(actual_main, (host, port))
			
	app = simpleapp_tk(None)
	app.title('Proxy running on localhost port: ' + str(port))
	app.mainloop()
	
if __name__ == '__main__':
	main()