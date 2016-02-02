@echo off

set data="F:\Jeux\Steam\SteamApps\common\Dark Souls Prepare to Die Edition\DATA"
set output="F:\Dev\Projets\DarkSoulsDev\ExtractedData"
set resources="F:\Dev\Projets\DarkSoulsDev\Ressources"

:: On Windows, the console will cause the program to fail on some Japanese
:: file names; we fix it with this var.
set PYTHONIOENCODING=utf_8

python -m dks_archives.main %data% %output% %resources%
