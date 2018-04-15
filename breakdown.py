import sys
import xml.dom.minidom
import csv
import codecs

def breakdown(fountain):
    f = csv.writer(sys.stdout)
    all_names = set()
    for n in fountain.getElementsByTagName("name"):
        all_names.add(n.firstChild.nodeValue)
        
    for s in fountain.getElementsByTagName("scene"):
        id = s.getAttribute("id")
        heading = s.getElementsByTagName("scene-heading")[0]
        try:
            setting = heading.getElementsByTagName("setting")[0].firstChild.nodeValue
        except IndexError:
            setting = None
        location = heading.getElementsByTagName("location")[0].firstChild.nodeValue
        try:
            tod = heading.getElementsByTagName("tod")[0].firstChild.nodeValue
        except IndexError:
            tod=None

        names = set()
        for n in s.getElementsByTagName("name"):
            names.add(n.firstChild.nodeValue)

        #print id, setting, location, tod, "; ". join(sorted(names))
        f.writerow(map(lambda s: s and codecs.encode(s, "utf-8"),
                       (id, setting, location, tod, "\n". join(sorted(names)))))

if __name__=="__main__":
    breakdown(xml.dom.minidom.parse(sys.stdin))
