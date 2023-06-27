CARDS = ["2", "3", "4", "5", "6", "7", "8", "9", "10", "K", "J","D","A"]  # Ace is either 1 or 11, figures are 10

def score(cards):
    """ How many points in the cards list? """
    s = 0
    for c in cards:
        if c in "KJD":
            s+=10
        elif c.isdigit():
            s+=int(c)

    for a in [c for c in cards if c in "A"]:
        if len([c for c in cards if c in "A"]) > 1 or s > 10:
            s+=1
        else:
            s+=11

    return s


if __name__ == "__main__":
    assert 10 == score(["2", "8"])
    assert 12 == score(["2", "K"])
    assert 21 == score(["D", "A"])
    assert 14 == score(["J", "3", "A"])
    assert 12 == score(["J", "A", "A"])
    print("Tests passed ")
