from dataclasses import dataclass
import re


@dataclass
class ParsedPage:
    rank: str
    inscription: str
    derniere_connexion: str
    gloire: int
    parties_jouees: int
    stats_dict_str: str

RANK_PATTERN = re.compile("<h1 class=\"playername\">(.*)</h1>")
STATS_REGEX = re.compile("pstats= (.*?),pstatsTotal")

#inscription, derniere_connexion, gloire, parties_jouees
ALL_IN_ONE_PATTERN = re.compile("<strong>Inscription :<\/strong> <span class=\"tooltips\" title=\"(.*?)\">.*?</span> </div> <div class=\"info-entry\"> <strong>Dernière connexion :</strong> <span class=\"tooltips\" title=\"(.*?)\">.*?</span> </div> </div> <div class=\"info-stats\"> <div class=\"lbl lbl-me lbl-primary\"> <i class=\"fa fa-gamepad\"></i> (.*?) Gloires accumulées </div>  <div class=\"lbl lbl-me\"> (.*?) Parties jouées </div>")


def parse_page_html(html: str) -> ParsedPage:
    rank, = re.search(RANK_PATTERN, html).groups()
    inscription, dc, gloire, pj = re.search(ALL_IN_ONE_PATTERN, html).groups()
    stats, = re.search(STATS_REGEX, html).groups()

    return ParsedPage(
        rank.strip(), inscription, dc,
        int(gloire.replace(" ", "")), int(pj.replace(" ", "")), stats
    )


NO_FRIEND_PATTERN = re.compile("La liste d'amis est vide.")
FRIEND_PATTERN = re.compile("<div class=\"head tooltips\" title=\"(.*?)\">")

def parse_friend_html(html: str) -> list[str] | None:
    result = re.findall(FRIEND_PATTERN, html)
    if len(result) == 0:
        return None
    return result
    
BAN_REGEX = re.compile("Ce joueur est banni \((.*?)\)")
def parse_ban(html: str) -> str | None:
    ban = re.findall(BAN_REGEX, html)
    if len(ban) == 0:
        return None
    
    return ban[0].replace("&agrave; vie / tr&egrave;s longtemps", "à vie / très longtemps")
