def get_data_by_year_range(self, first_year: str, last_year: str):
	"""
	Returns all file content belonging to the range of years specified.
	"""
	year_range = [str(year) for year in range(int(first_year), int(last_year) + 1)]
	return self.get_file_content_by_ranges(year_range)
def get_data_by_month_range(self, first_month, second_month):
	"""
	Returns all file content from all years, but within the specified month range.
	"""
	month_range = [
		f'0{i}' if i < 10 else str(i)
		for i in range(int(first_month), int(second_month))
	]
	return self.get_file_content_by_ranges(months=month_range)
def get_data_by_day_range(self, first_day, second_day):
	"""
	Returns all file content from all years and months,
	but within the specified day range.
	"""
	day_range = [
		f'0{i}' if i < 10 else str(i)
		for i in range(int(first_day), int(second_day))
	]
	return self.get_file_content_by_ranges(days=day_range)

"""
		
		all_paths = (
			os.path.join(path, basename)
			for path in paths for basename in os.listdir(path)  # Flattens
		)
		if basenames is None: return all_paths
		return (
			path for path in all_paths
			if os.path.splitext(os.path.basename(path))[0] in basenames
		)
"""

	def get_file_content_by_ranges(self, years:list= None, months: list= None, days:list= None):
		"""
		Returns a generator of file content belonging to the ranges of 
		years, months and days specified. If a parameter is not specified, the entire
		available range will be used.
		"""
		return self.get_file_content(self.__get_file_paths_by_ranges(years, months, days))


			print(f'available years: {reader.get_available_years()}')

	print(f'dirs to years {list(reader.get_dirs_by_years())}')

	month_paths = list(reader.__get_dirs_by_months(years=['2010', '2018']))

	print(f'dirs to months {month_paths}')

	day_paths = list(reader.__get_file_paths_by_ranges(years=['2010', '2018'], months= ['09'], days= ['12', '15']))

	print(f'dirs to days {day_paths}')