"""Module for answering to discord autocompletion requests"""
from datetime import datetime

#import dao
#import dao.requests as requests
import tools

REQUEST = "request"
STALE_IN = 120
autocomplete_cache = {REQUEST: {}}


def filter_options(ordered_elm, *args):
    """Navigate a nested dictionnary and returns the column after the last filter"""
    if args[0] is None:
        return ordered_elm.keys()
    sub_elem = ordered_elm.get(args[0])
    if sub_elem is not None:
        return filter_options(sub_elem, *args[1:])
    return []



def get_cache_request_options(guild_id, request_type=None, name=None, effect=None):
    """Get all the autocomplete options for requests"""
    cache = autocomplete_cache.get(REQUEST).get(guild_id)
    #If the cache doesnt exist or is stale
    if cache is None or cache[0].timestamp() + float(STALE_IN) < datetime.now().timestamp():
        #We will cache everything regardless of kwargs
        cache = [datetime.now(), tools.ordered_requests(guild_id)]
        autocomplete_cache[REQUEST][guild_id] = cache
    filtered_options = filter_options(cache[1], request_type, name, effect)
    return filtered_options


def autocomplete_from_options(options, word_start = ""):
    """Get all autocompletions available"""
    ell = len(word_start)
    if ell == 0:
        res = [{"name": w,"value": w} for w in options][:25]
    else:
        res = [{"name": w,"value": w} for w in options if w[: ell] == word_start][:25]
    return res
