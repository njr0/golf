from microdb.parser import Command
from microdb.shell import Shell

shell = Shell('default')
#shell = Shell('postgres')
filename = '2023-09-15.json'
cmd = Command('rcp',
              localpath=f'~/Documents/golf/{filename}',
              remotepath=f'golf/data/{filename}')
r = shell.do_rcp(cmd)
print(r)

cmd = Command('act', action='tracker')
r = shell.do_act(cmd)
print(r)


