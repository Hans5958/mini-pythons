import py7zr
import os
import shutil
import subprocess
import humanize
import traceback

IN_DIR = ".\\in"
TEMP_DIR = ".\\temp"
OUT_DIR = ".\\out"
INTACT_DIR = ".\\out-intact"
ERROR_DIR = ".\\out-error"

ULTRA_SETTINGS = ["-mx=9", "-mfb=64", "-md=64m", "-ms=256m"]
ULTRA_2_SETTINGS = ["-mx=9", "-mfb=273", "-md=64m", "-ms=256m"]
MAX_SETTINGS = ["-mx=9", "-mfb=273", "-ms", "-md=31", "-myx=9", "-mmt", "-md=1536m", "-mmf=bt3", "-mmc=10000", "-mpb=0", "-mlc=0"]

SIZE_LIMIT = 1024000000

os.makedirs(OUT_DIR, exist_ok=True)
os.makedirs(INTACT_DIR, exist_ok=True)
os.makedirs(ERROR_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)
shutil.rmtree(TEMP_DIR)
os.makedirs(TEMP_DIR)

TZ_PATH = "C:\\Program Files\\7-Zip\\7z.exe"

files = [f for f in os.listdir(IN_DIR) if os.path.isfile(os.path.join(IN_DIR, f))]

existing_files = []
existing_files.append([f for f in os.listdir(OUT_DIR) if os.path.isfile(os.path.join(OUT_DIR, f))])
existing_files.append([f for f in os.listdir(INTACT_DIR) if os.path.isfile(os.path.join(INTACT_DIR, f))])
existing_files.append([f for f in os.listdir(ERROR_DIR) if os.path.isfile(os.path.join(ERROR_DIR, f))])
existing_files = [item for sublist in existing_files for item in sublist]
existing_files = map(lambda x: os.path.basename(x), existing_files)
existing_files = list(existing_files)

def same_file_name_exist(item, reference):
	if item in reference:
		return True
	elif len(list(filter(lambda x: os.path.basename(x).startswith(os.path.splitext(os.path.basename(item))[0]), reference))) > 0:
		return True
	else:
		return False

for file in files:
	
	print()
	
	initial_size = os.stat(os.path.join(IN_DIR, file)).st_size 

	iteration = 0
	done = 0

	archive_temp_path = os.path.splitext(os.path.join(TEMP_DIR, file))[0] + '_'
	
	if same_file_name_exist(file, existing_files):
		print(f"Skipped: {file}")
		print("(File/archive existed on output dirs)")
		continue
	if not file.endswith("7z"):
		print(f"Skipped: {file}")
		print("(Archive is not a 7z archive)")
		shutil.copy(os.path.join(IN_DIR, file), os.path.join(INTACT_DIR, file))
		continue
	if py7zr.is_7zfile(file):
		print(f"Skipped: {file}")
		print("(Archive is not a valid 7z archive)")
		shutil.copy(os.path.join(IN_DIR, file), os.path.join(ERROR_DIR, file))
		continue
			
	try:

		with py7zr.SevenZipFile(os.path.join(IN_DIR, file), 'r') as archive:

			archive_files = archive.getnames()
			
			if same_file_name_exist(archive_files[0], existing_files):
				print(f"Skipped: {file}")
				print(f"(File existed on output dirs)")
				continue
			if len(archive_files) != 1:
				print(f"Skipped: {file}")
				print(f"(Archive has multiple files)")
				shutil.copy(os.path.join(IN_DIR, file), os.path.join(INTACT_DIR, file))
				continue
			if not archive_files[0].endswith(".mid"):
				print(f"Skipped: {file}")
				print(f"(File does not end with .mid)")
				shutil.copy(os.path.join(IN_DIR, file), os.path.join(INTACT_DIR, file))
				continue
			if archive.list()[0].uncompressed > SIZE_LIMIT:
				print(f"Skipped: {file}")
				print(f"(File is too big, {humanize.naturalsize(archive.list()[0].uncompressed)})")
				shutil.copy(os.path.join(IN_DIR, file), os.path.join(INTACT_DIR, file))
				continue
				
			os.makedirs(archive_temp_path)
				
			print(f"Now recompressing: {file} ({humanize.naturalsize(archive.list()[0].uncompressed)})")
			archive_file = archive_files[0]
			archive.extractall(archive_temp_path)
			print("File extracted. Compressing...")

			while done == 0:

				before_file = os.path.join(archive_temp_path, archive_file + ".xz" * iteration)
				iteration += 1
				after_file = os.path.join(archive_temp_path, archive_file + ".xz" * iteration)

				before_size = os.stat(before_file).st_size	

				subprocess.run([TZ_PATH, "a"] + ULTRA_2_SETTINGS + [after_file, before_file], stdout=subprocess.DEVNULL) #stdout=subprocess.DEVNULL
				# os.system(f"\"{TZ_PATH}\" a -m0=lzma -mx=9 -mfb=64 -md=64m -ms=256m \"{after_file}\" \"{before_file}\"")

				after_size = os.stat(after_file).st_size
				print(f"Iteration {iteration}: {humanize.naturalsize(before_size)} --> {humanize.naturalsize(after_size)} ({round(after_size*100/before_size, 5)}%)")

				if iteration != 1 and after_size/before_size > 0.5:
					done = 1

			if after_size/before_size > 0.95:
				iteration -= 1
				if after_size/before_size > 1:
					print(f"Last iteration is bigger. Using iteration {iteration}.")
				else:
					print(f"Last iteration has insignificant compression. Using iteration {iteration}.")
				after_file = os.path.join(archive_temp_path, archive_file + ".xz" * iteration)
				after_size = os.stat(after_file).st_size

			print(f"Final: {humanize.naturalsize(initial_size)} --> {humanize.naturalsize(after_size)} ({round(after_size*100/initial_size, 5)}%)")
			if initial_size > after_size:
				shutil.move(after_file, os.path.join(OUT_DIR, archive_file + ".xz" * iteration))
			else:
				print("(Not using the output. Copying input archive...)")
				shutil.copy(os.path.join(IN_DIR, file), os.path.join(INTACT_DIR, file))
				
		shutil.rmtree(archive_temp_path)
	
	except:
	
		traceback.print_exc()
		print(f"Skipped: {file}")
		print("(Something went wrong. Copying into the error folder...)")
		shutil.copy(os.path.join(IN_DIR, file), os.path.join(ERROR_DIR, file))

	
shutil.rmtree(TEMP_DIR)