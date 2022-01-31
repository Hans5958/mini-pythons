import py7zr
import os
import shutil
import subprocess
import humanize
import traceback
import unrar.rarfile
import zipfile
import hashlib

IN_DIR = ".\\in"
TEMP_DIR = ".\\temp"
OUT_DIR = ".\\out"
INTACT_DIR = ".\\out"
ERROR_DIR = ".\\out-discard"
NO_MID_DIR = '.\\out-discard'

SUPPORTED_FORMATS = ['7z', 'xz', 'zip', 'rar', 'mid']

ULTRA_SETTINGS = ["-mx=9", "-mfb=64", "-md=64m", "-ms=256m"]
ULTRA_2_SETTINGS = ["-mx=9", "-mfb=273", "-md=64m", "-ms=256m"]
MAX_SETTINGS = ["-mx=9", "-mfb=273", "-ms", "-md=31", "-myx=9", "-mmt", "-md=1536m", "-mmf=bt3", "-mmc=10000", "-mpb=0", "-mlc=0"]

SIZE_LIMIT = 10240000000

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(INTACT_DIR, exist_ok=True)
os.makedirs(ERROR_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
os.makedirs(NO_MID_DIR, exist_ok=True)
shutil.rmtree(TEMP_DIR)
os.makedirs(TEMP_DIR)

TZ_PATH = "C:\\Program Files\\7-Zip\\7z.exe"

files = [f for f in os.listdir(IN_DIR) if os.path.isfile(os.path.join(IN_DIR, f))]

existing_files = \
	[[f for f in os.listdir(OUT_DIR) if os.path.isfile(os.path.join(OUT_DIR, f))]] + \
	[[f for f in os.listdir(INTACT_DIR) if os.path.isfile(os.path.join(INTACT_DIR, f))]] + \
	[[f for f in os.listdir(ERROR_DIR) if os.path.isfile(os.path.join(ERROR_DIR, f))]] + \
	[[f for f in os.listdir(NO_MID_DIR) if os.path.isfile(os.path.join(NO_MID_DIR, f))]]
existing_files = [item for sublist in existing_files for item in sublist]
existing_files = map(lambda x: os.path.basename(x), existing_files)
existing_files = list(existing_files)

# print(existing_files)

def get_file_name(path):
	file_name = os.path.basename(path)
	file_extension = os.path.splitext(os.path.join(TEMP_DIR, path))[1][1:]
	file_extension = file_extension.lower()
	file_dirname = os.path.dirname(path)
	return [file_name, file_extension, file_dirname]

def same_file_name_exist(item, reference):
	if item in reference:
		return True
	elif len(list(filter(lambda x: os.path.basename(x).startswith(os.path.splitext(os.path.basename(item))[0]), reference))) > 0:
		return True
	else:
		return False

def get_short_hash(str):
	return hashlib.sha256(bytes(str, 'utf-8')).hexdigest()[:8]

def compress_mid(in_path, out_path):
	iteration = 1
	done = 0
	print(f'Compressing {in_path}...')
	[file_name, file_extension, file_dirname] = get_file_name(in_path)
	mid_temp_path = os.path.join(TEMP_DIR, 'mid_' + get_short_hash(file_name))
	os.makedirs(mid_temp_path)

	before_file = in_path
	initial_size = os.stat(in_path).st_size

	while done == 0:

		after_file = os.path.join(mid_temp_path, file_name + ".xz" * iteration)

		before_size = os.stat(before_file).st_size	

		subprocess.run([TZ_PATH, "a"] + ULTRA_2_SETTINGS + [after_file, before_file], stdout=subprocess.DEVNULL)

		after_size = os.stat(after_file).st_size
		print(f"Iteration {iteration}: {humanize.naturalsize(before_size)} --> {humanize.naturalsize(after_size)} ({round(after_size*100/before_size, 5)}%)")

		if iteration != 1 and after_size/before_size > 0.5:
			break

		before_file = os.path.join(mid_temp_path, file_name + ".xz" * iteration)
		iteration += 1

	if after_size/before_size > 0.95:
		iteration -= 1
		if after_size/before_size > 1:
			print(f"Last iteration is bigger. Using iteration {iteration}.")
		else:
			print(f"Last iteration has insignificant compression. Using iteration {iteration}.")
		after_file = os.path.join(mid_temp_path, file_name + ".xz" * iteration)
		after_size = os.stat(after_file).st_size

	print(f"Final: {humanize.naturalsize(initial_size)} --> {humanize.naturalsize(after_size)} ({round(after_size*100/initial_size, 5)}%)")
	shutil.move(after_file, os.path.join(out_path, file_name + ".xz" * iteration))
	shutil.rmtree(mid_temp_path)
	return os.path.join(out_path, file_name + ".xz" * iteration)

for file_rel_path in files:
	
	print()

	file_init_size = os.stat(os.path.join(IN_DIR, file_rel_path)).st_size 

	[file_name, file_ext, file_dir] = get_file_name(file_rel_path)

	content_temp_path = os.path.join(TEMP_DIR, get_short_hash(file_name))
	
	if same_file_name_exist(file_rel_path, existing_files):
		print(f"Skipped: {file_rel_path}")
		print("(File/archive existed on output dirs)")
		continue
	if not file_ext in SUPPORTED_FORMATS:
		print(f"Skipped: {file_rel_path}")
		print("(File type is not supported)")
		shutil.copy(os.path.join(IN_DIR, file_rel_path), NO_MID_DIR)
		continue
	# if py7zr.is_7zfile(file):
	# 	print(f"Skipped: {file}")
	# 	print("(Archive is not a valid 7z archive)")
	# 	shutil.copy(os.path.join(IN_DIR, file), os.path.join(ERROR_DIR, file))
	# 	continue

	os.makedirs(content_temp_path)

	print(f'Now: {file_rel_path}')
			
	try:

		if file_ext == 'mid':

			compress_mid(os.path.join(IN_DIR, file_rel_path), OUT_DIR)

		elif file_ext == 'rar' or file_ext == 'zip' or file_ext == '7z' or file_ext == 'xz':

			if file_ext == 'rar':
				with unrar.rarfile.RarFile(os.path.join(IN_DIR, file_rel_path)) as archive:
					archive.extractall(content_temp_path)
					
			elif file_ext == '7z' or file_ext == 'xz':
				with py7zr.SevenZipFile(os.path.join(IN_DIR, file_rel_path)) as archive:
					if archive.list()[0].uncompressed > SIZE_LIMIT:
						print(f"Skipped: {file_rel_path}")
						print(f"(File is too big, {humanize.naturalsize(archive.list()[0].uncompressed)})")
						shutil.copy(os.path.join(IN_DIR, file_rel_path), ERROR_DIR)
						shutil.rmtree(content_temp_path)
						continue
					else:
						archive.extractall(content_temp_path)

			elif file_ext == 'zip':
				with zipfile.ZipFile(os.path.join(IN_DIR, file_rel_path)) as archive:
					archive.extractall(content_temp_path)

			content_files = []
			for root, dirs, files in os.walk(content_temp_path):
				for file in files:
					#append the file name to the list
					content_files.append(os.path.normpath(os.path.join(root, file))[len(os.path.normpath(content_temp_path))+1:])

			if len(content_files) == 0:
				print(f"Skipped: {file_rel_path}")
				print("(Archive is empty)")
				shutil.copy(os.path.join(IN_DIR, file_rel_path), ERROR_DIR)
			elif not next((i for i in content_files if i.endswith('.mid')), None):
				print(f"Skipped: {file_rel_path}")
				print("(No .mid in the archive)")
				shutil.copy(os.path.join(IN_DIR, file_rel_path), NO_MID_DIR)

			elif len(content_files) == 1 and content_files[0].endswith('.mid') and os.path.splitext(get_file_name(content_files[0])[0])[0].replace('_', ' ', 99) == os.path.splitext(file_name)[0].replace('_', ' ', 99):
				# print("Only one .mid is found on the archive, and it has the same name with the archive. Directly compressing the .mid file.")
				print("Directly compressing the .mid file inside!")
				single_after_file = compress_mid(os.path.join(content_temp_path, content_files[0]), content_temp_path)
				single_after_size = os.stat(single_after_file).st_size
				
				print(f"Final: {humanize.naturalsize(file_init_size)} --> {humanize.naturalsize(single_after_size)} ({round(single_after_size*100/file_init_size, 5)}%)")
				if file_init_size > single_after_size:
					shutil.move(single_after_file, OUT_DIR)
				else:
					print("(Not using the output. Copying input archive...)")
					shutil.copy(os.path.join(IN_DIR, file_rel_path), INTACT_DIR)

			else:
				os.makedirs(os.path.join(content_temp_path, '#done'))
				os.makedirs(os.path.join(content_temp_path, '#temp'))

				for content_file_path in content_files:

					iteration = 0
					done = 0

					[content_file_name, content_file_ext, content_file_dir] = get_file_name(content_file_path)
					os.makedirs(os.path.join(content_temp_path, '#done', os.path.dirname(content_file_path)), exist_ok=True)
					os.makedirs(os.path.join(content_temp_path, '#temp', os.path.dirname(content_file_path)), exist_ok=True)

					if content_file_ext == 'mid':

						compress_mid(os.path.join(content_temp_path, content_file_path), os.path.join(content_temp_path, '#done'))

					else:
						
						print(f'Moving {content_file_path}...')
						shutil.move(os.path.join(content_temp_path, content_file_path), os.path.join(content_temp_path, '#done'))
				
				print('Creating an archive for the end result...')
				after_temp_file = os.path.join(content_temp_path, os.path.splitext(file_name)[0] + '.7z')

				subprocess.run([TZ_PATH, "a"] + ULTRA_2_SETTINGS + [after_temp_file, os.path.join(content_temp_path, '#done') + '/*'], stdout=subprocess.DEVNULL) #stdout=subprocess.DEVNULL
				after_size = os.stat(after_temp_file).st_size
				
				print(f"Final: {humanize.naturalsize(file_init_size)} --> {humanize.naturalsize(after_size)} ({round(after_size*100/file_init_size, 5)}%)")
				if file_init_size > after_size:
					shutil.move(after_temp_file, OUT_DIR)
				else:
					print("(Not using the output. Copying input archive...)")
					shutil.copy(os.path.join(IN_DIR, file_rel_path), INTACT_DIR)
		
		shutil.rmtree(content_temp_path)

	except:
	
		traceback.print_exc()
		print(f"Skipped: {file_rel_path}")
		print("(Something went wrong. Copying into the error folder...)")
		shutil.copy(os.path.join(IN_DIR, file_rel_path), ERROR_DIR)
		shutil.rmtree(content_temp_path)

	
shutil.rmtree(TEMP_DIR)