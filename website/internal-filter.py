from mod_python import apache
from sgmllib import SGMLParser

# FIXME: Import this class from some umic repository?
class CopySGMLParser( SGMLParser ):

	def __init__( self, file, xhtml=True):
		self.file = file
		self.xhtml = xhtml
		SGMLParser.__init__( self )
		
	def reset( self ):
		SGMLParser.reset( self )
  		self.copy_on = True

	def copy_tag(self, tag, attrs = []):
		self.file.write( "<" + tag )
		for name, value in attrs:
			self.file.write( " " )
			self.file.write( name + "=\"" + value + "\"" )
		self.file.write( ">" )
	
	def unknown_starttag( self, tag, attrs ):
		if self.copy_on:
			self.copy_tag(tag, attrs)
        
	def unknown_endtag( self, tag ):
		if self.copy_on:
			self.file.write( "</" + tag + ">" )

	def unknown_charref( self, ref ): 
		if self.copy_on:
			self.file.write( ref )
	
	def unknown_entityref( self, ref ): 
		if self.copy_on:
			self.file.write( ref )

	def handle_data(self, data ):
		if self.copy_on:
			self.file.write( data )

	def handle_comment(self, data):
		if self.copy_on:
			self.file.write( "<!--" + data + "-->")
	
	def handle_decl(self, data):
		if self.copy_on:
			self.file.write( "<!" + data + ">")
	
	def handle_pi(self, data):
		if self.copy_on:
			self.file.write( "<?" + data)
			## FIXME: This is a workaround for XSLT  not closing processing instructions when
			## in html output mode... yielding cascaded closing tags, i.e. ??????????>, 
			## upon a sequence of CopyParser calls
			if not data.endswith("?"):
				self.file.write("?");
			self.file.write(">");
	
	def handle_entityref(self, ref):
		if self.copy_on:
			self.file.write( "&" + ref +";")

	def handle_charref(	self, ref):
		if self.copy_on:
			self.file.write( "&#"  + ref + ";" )

	def report_unbalanced(self):
		# FIXME: Do something smarter!
		self.file.write("UNBALANCED")
		


class InternalFilter(CopySGMLParser):

	def __init__(self, file):
		self.depth = 0
		CopySGMLParser.__init__(self, file)

	def copy_tag(self, tag, attrs = []):
		out = "<" + tag
		for name, value in attrs:
			if name == "internal":
				self.CopyOff()
				return
			out += " " + name + "=\"" + value + "\""
		out += ">";
		self.file.write(out)
	
	def unknown_starttag( self, tag, attrs ):
		if self.copy_on:
			self.copy_tag(tag, attrs)
		else:
			self.depth += 1
        	
	def unknown_endtag( self, tag ):
		if self.copy_on:
			self.file.write( "</" + tag + ">" )
		else:
			self.CheckCopyOff()

	def start_a( self, attrs ):
		if not self.copy_on:
			return

		href = ""
		for n,v in attrs:
			if n == "href":
				href = v
				break
		if href.find("internal/") != -1:
			self.CopyOff()
		else:
			self.copy_tag("a", attrs)
		
	def CopyOff(self):
		self.copy_on = False
		self.depth = self.depth + 1

	def CheckCopyOff(self):
		self.depth -= 1
		if self.depth <= 0:
			self.depth = 0
			self.copy_on = True

	def Debug(self, msg):
		self.file.write("<h1>" + str(msg) + "</h1>")


def outputfilter(filter):
	IF = InternalFilter(filter)
	s = filter.read()
	while s:
		IF.feed(s)
		s = filter.read()

	if s is None:
		filter.close()
