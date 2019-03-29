import re


def remove_mentions(msg, current_guild):
    """Removes mentions from a message."""
    user_tags = set([c for c in msg.split(' ') if c[0:2] == '<@'])
    for user_tag in user_tags:
        userid = int(re.sub('\D', '', user_tag))
        username = current_guild.get_member(userid)
        if username is not None:
            username = username.display_name
            msg = msg.replace(user_tag, '@' + username)
        elif user_tag in msg:
            msg = msg.replace(user_tag, "@UNKNOWN_USER")
    return msg
