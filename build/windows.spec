# -*- mode: python -*-

block_cipher = None

path = os.path.abspath(os.path.join(".", os.pardir))
a = Analysis(['../main.py'],
             pathex=['path'],
             binaries=[],
             datas=[("../icons/error_icon.png","."),("../icons/add_icon.png","."),
			 ("../icons/delete_icon.png","."),("../icons/spinner.gif","."),("../icons/check_icon.png","."),
			 ("../icons/logo.png","."),("../icons/logo.ico","."),("../src/views/main.css",".")],
             hiddenimports=[],
             hookspath=[],
             runtime_hooks=[],
             excludes=[],
             win_no_prefer_redirects=False,
             win_private_assemblies=False,
             cipher=block_cipher,
             noarchive=False)
pyz = PYZ(a.pure, a.zipped_data,
             cipher=block_cipher)
exe = EXE(pyz,
          a.scripts,
          [],
          exclude_binaries=True,
          name='Chess Claim Tool',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          console=False,
		  icon='..\\icons\\logo.ico')
coll = COLLECT(exe,
               a.binaries,
               a.zipfiles,
               a.datas,
               strip=False,
               upx=True,
               name='Chess Claim Tool')
