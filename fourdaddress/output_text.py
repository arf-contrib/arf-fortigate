from string import Template

ENTRY_T = Template('edit ${hostname}\n'
        + '\tset type ipmask\n'
        + '\tset subnet ${ip} 255.255.255.255\n'
        + '\tset comment "${comment}"\n'
        + 'next\n')

VDOM_HEADER_T = Template('config vdom\n'
        + '\tedit ${vdom}\n')
VDOM_FOOTER = '\tnext\nend\n'


def output_text(entries, vdom='', prefix='', strip=False):
    lines_list = []
    for entry in entries:
        if prefix:
            entry.hostname = prefix + entry.hostname
        entry_lines = ENTRY_T.substitute(ip=entry.ip,
                hostname=entry.hostname,
                comment=entry.comment)
        lines_list.append(entry_lines)
    #always write command header/footer
    lines_list.insert(0, 'config firewall address')
    lines_list.append('end')
    lines_str = ''.join(l for l in lines_list)

    #if vdom is set, then indent all exist commands x2
    # and add vdom header/vdom footer
    if vdom:
        vdom_list = lines_str.split('\n')
        vdom_list = [f'\t\t{l}\n' for l in vdom_list]
        vdom_header = VDOM_HEADER_T.substitute(vdom=vdom)
        vdom_list.insert(0, vdom_header)
        vdom_list.append(VDOM_FOOTER)

        vdom_str = ''.join(l for l in vdom_list)
        lines_str = vdom_str

    #if strip is set, remove all leading whitespace (tabs)
    if strip:
        lines_str = lines_str.replace('\t', '')

    return lines_str
        
