import sys
import xml.dom.minidom
import collections

class Breakdown(object):
    def __init__(self):
        self.scenes = []
        self.locations = collections.defaultdict(list)
        self.characters = collections.defaultdict(list)

class Scene(object):
    def __init__(self, id, setting, location, tod):
        self.id = id
        self.setting = setting
        self.location = location
        self.tod = tod
        self.character_names = set()

class Element(object):
    def __init__(self, id):
        self.name = id
        self.scenes = []

# This is very basic. This algorithm is likely to break is some scenes
# already have numeric IDs--admittedly an unlikely usecase.
def number_scenes(fountain):
    seq=0
    for s in fountain.getElementsByTagName("scene"):
        ids=set()
        seq+=1
        id=s.getAttribute("id")
        if id:
            if id in ids:
                raise ValueError("duplicate section id: " + id)
        else:
            id = str(seq)
            while id in ids:
                seq+=1
                id = str(seq)
            s.setAttribute("id", id)
        ids.add(id)

def breakdown(fountain):
    number_scenes(fountain)

    bd = Breakdown()
        
    for e_s in fountain.getElementsByTagName("scene"):
        id = e_s.getAttribute("id")
        heading = e_s.getElementsByTagName("scene-heading")[0]
        try:
            setting = heading.getElementsByTagName("setting")[0].firstChild.nodeValue
        except IndexError:
            setting = None
        location = heading.getElementsByTagName("location")[0].firstChild.nodeValue
        try:
            tod = heading.getElementsByTagName("tod")[0].firstChild.nodeValue
        except IndexError:
            tod=None

        bs=Scene(id, setting, location, tod)
        bd.scenes.append(bs)

        bd.locations[location].append(id)

        for n in e_s.getElementsByTagName("name"):
            name = n.firstChild.nodeValue
            bs.character_names.add(name)

        for e_bd in e_s.getElementsByTagName("bd"):
            c = e_bd.getAttribute("class")
            if c=="character":
                bs.character_names.add(e_bd.getAttribute("idref"))

    return bd

if __name__=="__main__":
    bd = breakdown(xml.dom.minidom.parse(sys.stdin))

    print "LOCATIONS:"
    for l in sorted(bd.locations.keys()):
        print l, "("+str(len(bd.locations[l]))+"):", ", ".join(bd.locations[l])
    print

    print "SCENES:"
    for i, s in enumerate(bd.scenes):
        print i+1, s.id, "|", s.setting or "", "|", s.location, "|", s.tod
        print " characters:", ", ".join(sorted(s.character_names))

