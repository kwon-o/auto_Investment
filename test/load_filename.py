import glob

filename = glob.glob(r'C:/Users/KOJ/PycharmProjects/untitled/GitMaster/auto_Investment/csv/*.csv')

fileList = []
for i in filename:
    fileList.append(i.split("\\")[-1].split(".")[0])

print(fileList)


