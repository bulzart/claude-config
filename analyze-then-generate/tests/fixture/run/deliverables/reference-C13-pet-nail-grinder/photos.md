# Pet nail grinder - photo links

Links to images that belong to their owners. **Nothing was downloaded or stored**: each address was probed with a header request only. The angle is as the source labels it (the basis column), and no image has been looked at unless the 'looked at' column says so; open `photos.html` to see them in your browser. A link can expire or be hotlink-protected: save an image yourself if you need to keep it.

Coverage: **covered** - 9 link(s), 6 confirmed as images by a header request, 3 not confirmed; core angles present: front, back, left, right, top; confirmed: front, back, left, right, top; missing: none.

| id | angle | basis | source | link | https | may expire | bytes | variant | looked at | background | watermark | third-party brand marks | same variant | rights | status | image address | found on |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| PH001 | front | gallery-order | manufacturer | ok | no | no | 60000 | 2 L white | yes | clean | no | no | yes | stated-for-resellers | active | http://127.0.0.1:54710/front.png | https://maker.example/p/1 |
| PH002 | back | - | manufacturer | dead | no | no | 7 | - | no | - | - | - | - | unknown | rejected (HTTP 404: nothing at this address) | http://127.0.0.1:54710/missing.png | https://maker.example/p/1 |
| PH003 | back | - | manufacturer | not-image | no | no | 18 | - | no | - | - | - | - | unknown | rejected (Content-Type text/html: this address is not an image) | http://127.0.0.1:54710/notimg.png | https://maker.example/p/1 |
| PH004 | back | - | manufacturer | format | no | no | 6 | - | no | - | - | - | - | unknown | rejected (image/svg+xml is not a type the generation tools take as a reference (JPEG, PNG or WebP)) | http://127.0.0.1:54710/vector.svg | https://maker.example/p/1 |
| PH005 | back | - | manufacturer | format | no | no | 6 | - | no | - | - | - | - | unknown | rejected (image/gif is not a type the generation tools take as a reference (JPEG, PNG or WebP)) | http://127.0.0.1:54710/anim.gif | https://maker.example/p/1 |
| PH006 | back | - | manufacturer | blocked | no | no | 9 | - | no | - | - | - | - | unknown | rejected (x) | http://127.0.0.1:54710/blocked.png | https://maker.example/p/1 |
| PH007 | back | - | manufacturer | unchecked | no | no | - | - | no | - | - | - | - | unknown | active | http://127.0.0.1:54710/nohead.png | https://maker.example/p/1 |
| PH008 | back | - | manufacturer | unchecked | no | no | 60000 | - | no | - | - | - | - | unknown | active | http://127.0.0.1:54710/notype.png | https://maker.example/p/1 |
| PH009 | detail | - | manufacturer | ok | no | no | 900 | - | no | - | - | - | - | unknown | active | http://127.0.0.1:54710/tiny.png | https://maker.example/p/1 |
| PH010 | left | - | manufacturer | ok | no | yes | 60000 | - | no | - | - | - | - | unknown | active | http://127.0.0.1:54710/signed.png?Expires=1893456000&Signature=abc | https://maker.example/p/1 |
| PH011 | right | - | manufacturer | ok | no | no | 60000 | - | no | - | - | - | - | unknown | active | http://127.0.0.1:54710/redir-front.png | https://maker.example/p/1 |
| PH012 | top | - | manufacturer | unchecked | yes | no | - | - | no | - | - | - | - | unknown | active | https://example.invalid/front-https.png | https://maker.example/p/1 |
| PH013 | back | - | manufacturer | ok | no | no | 60000 | - | no | - | - | - | - | unknown | active | http://127.0.0.1:54710/back.png | https://maker.example/p/1 |
| PH014 | top | - | manufacturer | ok | no | no | 60000 | - | no | - | - | - | - | unknown | active | http://127.0.0.1:54710/top.webp | https://maker.example/p/1 |

Suggested reference set (the best link per view, chosen without looking at the images; a probe from this machine does not promise that another service can fetch an address):

- PH001 front: http://127.0.0.1:54710/front.png (ok, not https)
- PH013 back: http://127.0.0.1:54710/back.png (ok, not https)
- PH010 left: http://127.0.0.1:54710/signed.png?Expires=1893456000&Signature=abc (ok, not https, may expire)
- PH011 right: http://127.0.0.1:54710/redir-front.png (ok, not https)
- PH014 top: http://127.0.0.1:54710/top.webp (ok, not https)
