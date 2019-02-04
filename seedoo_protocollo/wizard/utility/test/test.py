import os

from BeautifulSoup import BeautifulSoup


def remove_img(content=""):
    ret = content

    while "<img" in ret:
        soup = BeautifulSoup(ret)
        soup.img.decompose()
        ret = str(soup)

    return ret


if __name__ == "__main__":
    mypath = os.path.dirname(__file__)
    body_files = [x for x in os.listdir(mypath) if x.startswith("body-") and os.path.isfile(x)]

    for body_file in body_files:
        print("Parsing %s" % body_file)

        fd = open(body_file, "r")
        body = fd.read()
        fd.close()

        result = remove_img(body)
        assert "<img" not in result
