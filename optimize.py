#!/usr/bin/python

# Copyright 2010 Craig Campbell
# 
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
# 
# http://www.apache.org/licenses/LICENSE-2.0
# 
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import sys, glob, re, math, os, shutil

def show_usage():
    print "USAGE:"
    print "./optimize.py path/to/css path/to/views\n"
    print "OPTIONAL PARAMS:"
    print "--css-file {file_name}       file to use for optimized css (defaults to optimized.css)"
    print "--view-ext {extension}       sets the extension to use for the view directory (defaults to html)"
    print "--rewrite-css                if this arg is present then header css includes are rewritten in the new views"
    print "--help                       shows this menu"

# required arguments
try:
    css_dir = sys.argv[1].rstrip("/")
    view_dir = sys.argv[2].rstrip("/")
except IndexError:
    show_usage()
    sys.exit()

# properties
css_file = "optimized.css"
view_extension = "html"
rewrite_css = False
letters = map(chr, range(97, 123))
all_ids = []
all_classes = []
id_index = 0
class_index = 0
relative_path = ""
if view_dir.count('/') == css_dir.count('/'):
    relative_path = "../"

# check for optional parameters
for key, arg in enumerate(sys.argv):
    next = key + 1
    if arg == "--help":
        show_usage()
        sys.exit()
    elif arg == "--rewrite-css":
        rewrite_css = True
    elif arg == "--css-file":
        css_file = sys.argv[next]
    elif arg == "--view-ext":
        view_extension = sys.argv[next]

css_file_minimized = css_file.replace(".css", ".min.css");

# remove the css file we are going to be recreating
try:
    os.unlink(css_dir + "/" + css_file)
except:
    pass

try:
    os.unlink(css_dir + "/" + css_file_minimized)
except:
    pass

#
# adds ids to the master list of ids
#
# @param list ids_found
# @return void
#
def addIds(ids_found):
    for id in ids_found:
        if id[1] is ';':
            continue
        if id[0] not in all_ids:
            all_ids.append(id[0])

#
# adds classes to the master list of classes
#
# @param list classes_found
# @return void
#
def addClasses(classes_found):
    for class_name in classes_found:
        if class_name not in all_classes:
            all_classes.append(class_name)

#
# gets the letter of the class based on what number class or id this is
#
# @param int index
# @return string
#
def getLetterAtIndex(index):
    letter_count = int(math.ceil(index / 26) + 1)
    letter = letters[index % 26]
    string = ''
    for i in range(0, letter_count):
        string = string + letter
    return string

#
# replaces css rules with optimized names
#
# @param dictionary dictionary
# @param string content
# @return string
#
def replaceCss(dictionary, content):
    for key, value in dictionary.items():
        content = content.replace(key + "{", value + "{")
        content = content.replace(key + " {", value + " {")
        content = content.replace(key + "#", value + "#")
        content = content.replace(key + " #", value + " #")
        content = content.replace(key + ".", value + ".")
        content = content.replace(key + " .", value + " .")
        content = content.replace(key + ",", value + ",")
    return content

#
# replaces classes and ids with new values in a view file
#
# @uses replaceHtml
# @param string file_path
# @return string
#
def optimizeHtml(file_path):
    file = open(file_path)
    contents = file.read()
    contents = replaceHtml(id_map, contents)
    contents = replaceHtml(class_map, contents)
    return contents

#
# replaces html in views from lists of classes and ids
#
# @param dictionary dictionary
# @param string content
# return string
#
def replaceHtml(dictionary, content):
    initial_content = content
    for key, value in dictionary.items():
        first_char = key[0]
        key = key[1:]
        value = value[1:]
        # ids are easy
        if first_char is '#':
            content = content.replace("id=\"" + key + "\"", "id=\"" + value + "\"")
            continue

        # classes are hard
        class_blocks = re.findall(r'class="(.*)"', content)
        for class_block in class_blocks:
            new_block = class_block.replace(key, value)
            content = content.replace("class=\"" + class_block + "\"", "class=\"" + new_block + "\"")
        # print class_blocks
    if content:
        return content

    return initial_content


# loop through the css files once to get all the classes and ids we are going to need
files = glob.glob(css_dir + "/*.css")
for file in files:
    file = open(file, "r")
    contents = file.read()
    file.close()

    # find ids in file
    ids_found = re.findall(r'(#\w+)(;)?', contents)

    # find classes in file
    classes_found = re.findall(r'(?!\.[0-9])\.\w+', contents)

    # add what we found to the master lists
    addIds(ids_found)
    addClasses(classes_found)

# create definitions mapping old names to new ones
# .a => .killer_class, #a => #sweet_id
class_map = {}
for class_name in all_classes:
    class_map[class_name] = "." + getLetterAtIndex(class_index)
    class_index = class_index + 1

id_map = {}
for id in all_ids:
    id_map[id] = "#" + getLetterAtIndex(id_index)
    id_index = id_index + 1

file_path = css_dir + "/" + css_file
master_file = open(file_path, "w");

# loop through the files a second time to rename the classes/ids based on the definitions
files = glob.glob(css_dir + "/*.css")
for file in files:
    name = file
    if file == file_path:
        continue

    print "adding " + name + " to " + file_path
    file = open(file, "r")
    contents = file.read()
    contents = replaceCss(class_map, contents)
    contents = replaceCss(id_map, contents)
    master_file.writelines("/*\n * " + name + "\n */\n" + contents + "\n\n");

master_file.close()
master_file = None

# open up the master file we just wrote to to grab the final contents
master_file = open(file_path, "r");
contents = master_file.read()
master_file.close()

# minimize the stuff
from minimize import minimize
contents = minimize(contents)

# write it back to minimized file
new_file = open(css_dir + "/" + css_file_minimized, "w")
new_file.write(contents)
new_file.close()
new_file = None

# now it is time to replace the html values
new_view_dir = view_dir + "_optimized"
try:
    shutil.rmtree(new_view_dir)
except:
    pass

# create a new directory to hold all the new views
os.mkdir(new_view_dir)

# loop through all of the views and do the magic stuff
files = glob.glob(view_dir + "/*." + view_extension)
for file in files:
    i = 0
    file_name = file.replace(view_dir + "/", "")
    print "optimizing " + file_name
    new_content = optimizeHtml(file)
    new_lines = []
    for line in new_content.split("\n"):
        if "text/css" not in line or rewrite_css is False:
            new_lines.append(line)
            continue

        if i is 0:
            new_lines.append('<link href="' + relative_path + css_dir + "/" + css_file_minimized + '" rel="stylesheet" type="text/css" />')
            i = i + 1

    new_content = "\n".join(map(str, new_lines))

    new_file = open(new_view_dir + "/" + file_name, "w")
    new_file.write(new_content)
    new_file.close()

print "all done!"
