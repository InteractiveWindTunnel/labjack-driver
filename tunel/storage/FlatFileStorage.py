from ..device import MeasuresStorage
import csv
import locale
class FlatFileStorage(MeasuresStorage):
	_file=None
	filename = ''
	def __init__(self):
		pass
	def put_data(self,data):
		out=[]
		for tmp in data:
			out.append(locale.str(tmp))
		self._writer.writerow(out)
	def open_series(self):
		self._file = open(self.filename,"wb")
		self._writer = csv.writer(self._file,dialect='excel', delimiter=';')
	def close_series(self):
		self._file.close()
		self._file = None

