import py7zr
import os
import shutil
import subprocess
import humanize
import traceback
import unrar.rarfile
import zipfile
import hashlib
from pathlib import Path

IN_DIR = ".\\in"
TEMP_DIR = ".\\temp"
OUT_DIR = ".\\out"
INTACT_DIR = ".\\out-discard" #discard
ERROR_DIR = ".\\out-discard" #discard
NO_MID_DIR = '.\\out-discard'

SUPPORTED_FORMATS = [
	'7z', 'xz', 'zip', 'rar', 
	'mid', 'flp'
]

ULTRA_SETTINGS = ["-mx=9", "-mfb=64", "-md=64m", "-ms=256m"]
ULTRA_2_SETTINGS = ["-mx=9", "-mfb=273", "-md=64m", "-ms=256m"]
MAX_SETTINGS = ["-mx=9", "-mfb=273", "-ms", "-md=31", "-myx=9", "-mmt", "-md=1536m", "-mmf=bt3", "-mmc=10000", "-mpb=0", "-mlc=0"]
SELECTED_SETTINGS = ULTRA_2_SETTINGS

SIZE_LIMIT = 10240000000

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(INTACT_DIR, exist_ok=True)
os.makedirs(ERROR_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(NO_MID_DIR, exist_ok=True)
shutil.rmtree(TEMP_DIR)
os.makedirs(TEMP_DIR)

TZ_PATH = "C:\\Program Files\\7-Zip\\7z.exe"

#files = [f for f in os.listdir(IN_DIR) if os.path.isfile(Path(IN_DIR, f))]
files = []

for r, d, f in os.walk(IN_DIR):
	for file in f:
		files.append(os.path.sep.join(Path(r, file).parts[1:]))

existing_files = []
for r, d, f in os.walk(OUT_DIR):
	for file in f:
		existing_files.append(os.path.sep.join(Path(r, file).parts[1:]))
for r, d, f in os.walk(INTACT_DIR):
	for file in f:
		existing_files.append(os.path.sep.join(Path(r, file).parts[1:]))
for r, d, f in os.walk(ERROR_DIR):
	for file in f:
		existing_files.append(os.path.sep.join(Path(r, file).parts[1:]))
for r, d, f in os.walk(NO_MID_DIR):
	for file in f:
		existing_files.append(os.path.sep.join(Path(r, file).parts[1:]))

def get_file_name(path):
	file_name = os.path.basename(path)
	file_extension = os.path.splitext(Path(TEMP_DIR, path))[1][1:]
	file_extension = file_extension.lower()
	file_dirname = os.path.dirname(path)
	return [file_name, file_extension, file_dirname]

def same_file_name_exist(item, reference):
	if item in reference:
		return True
	elif len(list(filter(lambda x: x.startswith(item), reference))) > 0:
		return True
	else:
		return False

def get_short_hash(strin):
	strin = str(strin)
	return hashlib.sha256(bytes(strin, 'utf-8')).hexdigest()[:8]

def compress_mid(in_path, out_path):
	
	iteration = 1
	done = 0
	print(f'Compressing {in_path}...')
	[file_name, file_extension, file_dirname] = get_file_name(in_path)
	mid_temp_path = Path(TEMP_DIR, 'mid_' + get_short_hash(in_path))
	os.makedirs(mid_temp_path)

	before_file = in_path
	initial_size = os.stat(in_path).st_size

	while done == 0:

		after_file = Path(mid_temp_path, file_name + ".7z" * (1 if iteration > 0 else 0) + ".xz" * (iteration - 1))

		before_size = os.stat(before_file).st_size	

		# print('.' + os.path.sep + str(before_file))
		# input()
		subprocess.run([TZ_PATH, "a"] + SELECTED_SETTINGS + [after_file, '.' + os.path.sep + str(before_file)], stdout=subprocess.DEVNULL)

		after_size = os.stat(after_file).st_size
		print(f"Iteration {iteration}: {humanize.naturalsize(before_size)} --> {humanize.naturalsize(after_size)} ({round(after_size*100/before_size, 5)}%)")

		if iteration != 1 and after_size/before_size > 0.5:
			break

		before_file = Path(mid_temp_path, file_name + ".7z" * (1 if iteration > 0 else 0) + ".xz" * (iteration - 1))
		iteration += 1

	if after_size/before_size > 0.95:
		iteration -= 1
		if after_size/before_size > 1:
			print(f"Last iteration is bigger. Using iteration {iteration}.")
		else:
			print(f"Last iteration has insignificant compression. Using iteration {iteration}.")
		after_file = Path(mid_temp_path, file_name + ".7z" * (1 if iteration > 0 else 0) + ".xz" * (iteration - 1))
		after_size = os.stat(after_file).st_size

	print(f"Final: {humanize.naturalsize(initial_size)} --> {humanize.naturalsize(after_size)} ({round(after_size*100/initial_size, 5)}%)")
	shutil.move(after_file, Path(out_path, file_name + ".7z" * (1 if iteration > 0 else 0) + ".xz" * (iteration - 1)))
	shutil.rmtree(mid_temp_path)
	return Path(out_path, file_name + ".7z" * (1 if iteration > 0 else 0) + ".xz" * (iteration - 1))

for file_rel_path in files:

	print()
	file_init_size = os.stat(Path(IN_DIR, file_rel_path)).st_size 

	[file_name, file_ext, file_dir] = get_file_name(file_rel_path)

	content_temp_path = Path(TEMP_DIR, get_short_hash(file_rel_path))
	
	if same_file_name_exist(file_rel_path, existing_files):
		print(f"Skipped: {file_rel_path}")
		print("(File/archive existed on output dirs)")
		continue
	if not file_ext in SUPPORTED_FORMATS:
		print(f"Skipped: {file_rel_path}")
		print("(File type is not supported)")
		Path(NO_MID_DIR, file_rel_path).parents[0].mkdir(parents=True, exist_ok=True)
		shutil.copy(Path(IN_DIR, file_rel_path), Path(NO_MID_DIR, file_rel_path))
		continue
	# if py7zr.is_7zfile(file):
	# 	print(f"Skipped: {file}")
	# 	print("(Archive is not a valid 7z archive)")
	# 	shutil.copy(Path(IN_DIR, file), Path(ERROR_DIR, file))
	# 	continue

	os.makedirs(content_temp_path)

	print(f'Now: {file_rel_path}')
			
	try:

		if file_ext == 'mid':

			Path(OUT_DIR, file_rel_path).parents[0].mkdir(parents=True, exist_ok=True)
			compress_mid(Path(IN_DIR, file_rel_path), Path(OUT_DIR, file_rel_path).parents[0])

		elif file_ext == 'flp':

			Path(OUT_DIR, file_rel_path).parents[0].mkdir(parents=True, exist_ok=True)
			compress_mid(Path(IN_DIR, file_rel_path), Path(OUT_DIR, file_rel_path).parents[0])

		elif file_ext == 'rar' or file_ext == 'zip' or file_ext == '7z' or file_ext == 'xz':

			if file_ext == 'rar':
				with unrar.rarfile.RarFile(str(Path(IN_DIR, file_rel_path))) as archive:
					archive.extractall(str(content_temp_path))
					
			elif file_ext == '7z' or file_ext == 'xz':
				with py7zr.SevenZipFile(Path(IN_DIR, file_rel_path)) as archive:
					if archive.list()[0].uncompressed > SIZE_LIMIT:
						print(f"Skipped: {file_rel_path}")
						print(f"(File is too big, {humanize.naturalsize(archive.list()[0].uncompressed)})")
						Path(ERROR_DIR, file_rel_path).parents[0].mkdir(parents=True, exist_ok=True)
						shutil.copy(Path(IN_DIR, file_rel_path), Path(ERROR_DIR, file_rel_path).parents[0])
						shutil.rmtree(content_temp_path)
						continue
					else:
						archive.extractall(content_temp_path)

			elif file_ext == 'zip':
				with zipfile.ZipFile(Path(IN_DIR, file_rel_path)) as archive:
					archive.extractall(content_temp_path)

			content_files = []
			for r, d, files in os.walk(content_temp_path):
				for file in files:
					#append the file name to the list
					content_files.append(os.path.normpath(Path(r, file))[len(os.path.normpath(content_temp_path))+1:])

			if len(content_files) == 0:
				print(f"Skipped: {file_rel_path}")
				print("(Archive is empty)")
				Path(ERROR_DIR + os.path.sep + file_rel_path).parents[0].mkdir(parents=True, exist_ok=True)
				shutil.copy(Path(IN_DIR, file_rel_path), Path(ERROR_DIR, file_rel_path).parents[0])
			elif not next((i for i in content_files if i.endswith('.mid')), None):
				print(f"Skipped: {file_rel_path}")
				print("(No .mid in the archive)")
				Path(NO_MID_DIR + os.path.sep + file_rel_path).parents[0].mkdir(parents=True, exist_ok=True)
				shutil.copy(Path(IN_DIR, file_rel_path), Path(NO_MID_DIR, file_rel_path).parents[0])

			elif len(content_files) == 1 and (content_files[0].endswith('.mid') or content_files[0].endswith('.flp')) and os.path.splitext(get_file_name(content_files[0])[0])[0].replace('_', ' ', 99) == os.path.splitext(file_name)[0].replace('_', ' ', 99):
				# print("Only one .mid is found on the archive, and it has the same name with the archive. Directly compressing the .mid file.")
				print("Directly compressing the .mid file inside!")
				if same_file_name_exist(content_files[0], existing_files):
					print(f"Skipped: {content_files[0]}")
					print("(File/archive existed on output dirs)")
					continue
				single_after_file = compress_mid(Path(content_temp_path, content_files[0]), content_temp_path)
				single_after_size = os.stat(single_after_file).st_size
				
				print(f"Final: {humanize.naturalsize(file_init_size)} --> {humanize.naturalsize(single_after_size)} ({round(single_after_size*100/file_init_size, 5)}%)")
				if file_init_size > single_after_size:
					Path(OUT_DIR + os.path.sep + file_rel_path).parents[0].mkdir(parents=True, exist_ok=True)
					shutil.move(single_after_file, Path(OUT_DIR, file_rel_path).parents[0])
				else:
					print("(Not using the output. Copying input archive...)")
					Path(INTACT_DIR + os.path.sep + file_rel_path).parents[0].mkdir(parents=True, exist_ok=True)
					shutil.copy(Path(IN_DIR, file_rel_path), Path(INTACT_DIR, file_rel_path).parents[0])

			else:
				os.makedirs(Path(content_temp_path, '#done'))
				os.makedirs(Path(content_temp_path, '#temp'))

				for content_file_path in content_files:

					iteration = 0
					done = 0

					[content_file_name, content_file_ext, content_file_dir] = get_file_name(content_file_path)
					os.makedirs(Path(content_temp_path, '#done', os.path.dirname(content_file_path)), exist_ok=True)
					os.makedirs(Path(content_temp_path, '#temp', os.path.dirname(content_file_path)), exist_ok=True)

					if content_file_ext == 'mid' or content_file_ext == 'flp':

						compress_mid(Path(content_temp_path, content_file_path), Path(content_temp_path, '#done'))

					else:
						
						print(f'Moving {content_file_path}...')
						shutil.move(Path(content_temp_path, content_file_path), Path(content_temp_path, '#done'))
				
				print('Creating an archive for the end result...')
				after_temp_file = Path(content_temp_path, os.path.splitext(file_name)[0] + '.7z')

				subprocess.run([TZ_PATH, "a"] + ULTRA_2_SETTINGS + [after_temp_file, f'.{os.path.sep}' + os.path.join(content_temp_path, '#done') + f'{os.path.sep}*'], stdout=subprocess.DEVNULL) #stdout=subprocess.DEVNULL
				after_size = os.stat(after_temp_file).st_size
				
				print(f"Final: {humanize.naturalsize(file_init_size)} --> {humanize.naturalsize(after_size)} ({round(after_size*100/file_init_size, 5)}%)")
				if file_init_size > after_size:
					Path(OUT_DIR + os.path.sep + file_rel_path).parents[0].mkdir(parents=True, exist_ok=True)
					shutil.move(after_temp_file, Path(OUT_DIR, file_rel_path).parents[0])
				else:
					print("(Not using the output. Copying input archive...)")
					Path(INTACT_DIR + os.path.sep + file_rel_path).parents[0].mkdir(parents=True, exist_ok=True)
					shutil.copy(Path(IN_DIR, file_rel_path), Path(INTACT_DIR, file_rel_path).parents[0])
		
		shutil.rmtree(content_temp_path)

	except:
	
		traceback.print_exc()
		print(f"Skipped: {file_rel_path}")
		print("(Something went wrong. Copying into the error folder...)")
		Path(ERROR_DIR + os.path.sep + file_rel_path).parents[0].mkdir(parents=True, exist_ok=True)
		shutil.copy(Path(IN_DIR, file_rel_path), Path(INTACT_DIR, file_rel_path).parents[0])
		shutil.rmtree(content_temp_path)

	
shutil.rmtree(TEMP_DIR)