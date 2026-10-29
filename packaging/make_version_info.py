"""Generate a Windows version resource file for Netckore."""

from pathlib import Path

version_file = Path(__file__).parent / "version_info.txt"


def main():
    version = "0.1.0"
    content = f"""VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(0, 1, 0, 0),
    prodvers=(0, 1, 0, 0),
    mask=0x3f,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo(
      [
        StringTable(
          '040904B0',
          [
            StringStruct('FileDescription', 'Netckore - Herramienta de conexión a internet'),
            StringStruct('FileVersion', '0.1.0'),
            StringStruct('ProductVersion', '0.1.0'),
            StringStruct('CompanyName', '0noxtackore'),
            StringStruct('ProductName', 'Netckore'),
            StringStruct('LegalCopyright', 'Copyright (c) 2026 Netckore Team')
          ]
        )
      ]
    ),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"""
    version_file.write_text(content, encoding="utf-8")
    print("version_info.txt generated")


if __name__ == "__main__":
    main()