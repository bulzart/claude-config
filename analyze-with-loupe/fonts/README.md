# fonts: the fonts Static projects point to

A CapCut project shows a text in its font only while the font file stays where the project points. CapCut's own fonts sit in its
version folder (`%LOCALAPPDATA%\CapCut\Apps\<version>\Resources\Font`), which an update replaces, and the fonts it downloads for its
templates sit in its cache (`%LOCALAPPDATA%\CapCut\User Data\Cache\AITextTemplate\Resource\<id>`), which CapCut may clear. A text
whose file is gone shows in CapCut's default font. So a Static plan points its captions and labels at a copy in this folder
(`T capcut-font --list` lists it first, with `kept_by` for every font; reference/static §7).

Copied 2026-11-07 from CapCut's template cache. Each one is a Google Font under the SIL Open Font License 1.1, which allows copying and
use in videos:

| file | family | where it came from |
|---|---|---|
| SigmarOne-Regular.ttf | Sigmar One | CapCut cache 5438151499500863920 |
| Coiny-Regular.ttf | Coiny | CapCut cache 11907617677891257820 |
| DynaPuff-SemiBold.ttf | DynaPuff SemiBold | CapCut cache 629998386168121261 |
| Anton-Regular.ttf | Anton | CapCut cache 5962597139823241267 |
| Montserrat-Bold.otf | Montserrat Bold | CapCut cache 4387537725143947161 |
| Corben-Bold.ttf | Corben Bold | CapCut cache 12963064053485014624 |
| AmaticSC-Bold.ttf | Amatic SC Bold | CapCut cache 1629602365863457004 |

Not copied: CapCut's own "ZY" fonts, Stilu and Bounce House (their licences are not known), and CapCut Sans (CapCut's own font).
Another open font is added here the same way, with its row.
