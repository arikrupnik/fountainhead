import sys
import xml.dom.minidom
import collections
import codecs

from fountainhead import ownerDocument, subElement, appendText, subElementWithText, findElementByAttributeValue

# This is very basic. This algorithm is likely to break if some scenes
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

    for e_s in fountain.getElementsByTagName("scene"):

        character_names = set()

        for n in e_s.getElementsByTagName("name"):
            name = n.firstChild.nodeValue
            character_names.add(name)

        for e_bd in e_s.getElementsByTagName("bd"):
            c = e_bd.getAttribute("class")
            if c=="character":
                character_names.add(e_bd.getAttribute("idref"))

        e_bd = subElement(e_s, "breakdown")
        for c in sorted(character_names):
            subElementWithText(e_bd, "character-ref", c)

if __name__=="__main__":
    fountain = xml.dom.minidom.parse(sys.stdin)
    breakdown(fountain)

    print codecs.encode(fountain.toxml(), "utf-8")
