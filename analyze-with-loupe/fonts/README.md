# fonts: the fonts Static projects point to

A CapCut project shows a text in its font only while the font file stays where the project points. CapCut's own fonts sit in its
version folder (`%LOCALAPPDATA%\CapCut\Apps\<version>\Resources\Font`), which an update replaces, and the fonts it downloads for its
templates sit in its cache (`%LOCALAPPDATA%\CapCut\User Data\Cache\AITextTemplate\Resource\<id>`), which CapCut may clear. A text
whose file is gone shows in CapCut's default font. So a Static plan points its captions and labels at a copy in this folder
(`T capcut-font --list` lists it first, with `kept_by` for every font; reference/static §7).

Every font here is under the SIL Open Font License 1.1 or the Apache License 2.0, which allow copying and use in videos. Another open
font is added the same way, with its row.

## Copied from CapCut's template cache (2026-11-07)

| file | family | licence |
|---|---|---|
| SigmarOne-Regular.ttf | Sigmar One | OFL |
| Coiny-Regular.ttf | Coiny | OFL |
| DynaPuff-SemiBold.ttf | DynaPuff SemiBold | OFL |
| Anton-Regular.ttf | Anton | OFL |
| Montserrat-Bold.otf | Montserrat Bold | OFL |
| Corben-Bold.ttf | Corben Bold | OFL |
| AmaticSC-Bold.ttf | Amatic SC Bold | OFL |

## Downloaded (2026-11-07): popular YouTube caption fonts

From the Fontsource CDN (`https://cdn.jsdelivr.net/fontsource/fonts/<id>@latest/latin-<weight>-normal.ttf`): one static weight each,
the latin subset (English and most western European letters). A few files carry the variable font's default name inside (Montserrat
Black reads "Montserrat Thin", style Black); CapCut loads them by file, and their letters are the heavy weight (a specimen was drawn).

| file | family | licence |
|---|---|---|
| Montserrat-ExtraBold.ttf, Montserrat-Black.ttf | Montserrat 800, 900 | OFL |
| Poppins-Bold.ttf, Poppins-ExtraBold.ttf, Poppins-Black.ttf | Poppins 700, 800, 900 | OFL |
| BebasNeue-Regular.ttf | Bebas Neue | OFL |
| Oswald-Bold.ttf | Oswald 700 | OFL |
| Roboto-Black.ttf | Roboto 900 | OFL |
| Inter-ExtraBold.ttf, Inter-Black.ttf | Inter 800, 900 | OFL |
| LuckiestGuy-Regular.ttf | Luckiest Guy | Apache 2.0 |
| Bangers-Regular.ttf | Bangers | OFL |
| LilitaOne-Regular.ttf | Lilita One | OFL |
| ArchivoBlack-Regular.ttf | Archivo Black | OFL |
| TitanOne-Regular.ttf | Titan One | OFL |
| Rubik-ExtraBold.ttf, Rubik-Black.ttf | Rubik 800, 900 | OFL |
| Nunito-Black.ttf | Nunito 900 | OFL |
| Fredoka-Bold.ttf | Fredoka 700 | OFL |
| PermanentMarker-Regular.ttf | Permanent Marker | Apache 2.0 |
| Bungee-Regular.ttf | Bungee | OFL |
| LeagueSpartan-Black.ttf | League Spartan 900 | OFL |
| Barlow-Black.ttf | Barlow 900 | OFL |
| Kanit-ExtraBold.ttf | Kanit 800 | OFL |
| OpenSans-ExtraBold.ttf | Open Sans 800 | OFL |
| Lato-Black.ttf | Lato 900 | OFL |
| Raleway-Black.ttf | Raleway 900 | OFL |
| Baloo2-ExtraBold.ttf | Baloo 2 800 | OFL |
| Chewy-Regular.ttf | Chewy | Apache 2.0 |
| BowlbyOne-Regular.ttf | Bowlby One | OFL |
| PassionOne-Bold.ttf | Passion One 700 | OFL |
| PaytoneOne-Regular.ttf | Paytone One | OFL |
| RussoOne-Regular.ttf | Russo One | OFL |
| FjallaOne-Regular.ttf | Fjalla One | OFL |

Not here: CapCut's own "ZY" fonts, Stilu and Bounce House (their licences are not known), CapCut Sans (CapCut's own font), and the
popular paid or personal-use-only faces (The Bold Font, Komika Axis, Gotham, Proxima Nova, Futura).
