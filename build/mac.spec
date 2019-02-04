# -*- mode: python -*-

block_cipher = None

path = os.path.abspath(os.path.join(".", os.pardir))
a = Analysis(['../main.py'],
             pathex=[path],
             binaries=[],
             datas=[("../icons/error_icon.png","."),("../icons/add_icon.png","."),("../icons/delete_icon.png","."),("../icons/spinner.gif","."),("../icons/check_icon.png","."),("../icons/logo.png","."),("../main.css",".")],
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
          a.binaries,
          a.zipfiles,
          a.datas,
          [],
          name='main',
          debug=False,
          bootloader_ignore_signals=False,
          strip=False,
          upx=True,
          runtime_tmpdir=None,
          console=False )

app = BUNDLE(exe,
      name='Chess Claim Tool.app',
      icon = "../icons/logo.icns",
          info_plist={
              'NSHighResolutionCapable':True,
              'NSAppleScriptEnabled': False,
              'CFBundleIdentifier': 'com.brainfriz.chess-claim-tool',
              'CFBundleInfoDictionaryVersion':'0.1',
              'CFBundleShortVersionString':'0.1.0',
              'NSHumanReadableCopyright':'© 2019 Serntedakis Athanasios',
              'CFBundleDocumentTypes': [
                    {
                      'CFBundleTypeName': 'Chess Check Claims',
                      'LSItemContentTypes': ['com.brainfriz.chess-claim-tool'],
                      'LSHandlerRank': 'Owner'
                      }
                  ]
                },
            )
