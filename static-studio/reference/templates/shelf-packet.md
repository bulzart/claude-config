# A shelf of videos

{{STANCE}}

You are on YouTube with a little time and nothing decided. These are the videos on your screen, each as its title and
its small picture described in words. Some of them exist already and some do not exist yet; you are not told which,
and it does not matter.

{{SHELF}}

Answer from your first reaction, as that viewer, without being polite. Write your answer as one JSON object to
`{{OUT}}`:

```json
{"would_click": [3, 1],
 "would_scroll_past": [2, 5],
 "per_item": [{"n": 1, "expects": "what you think this video will give you, in one sentence",
               "pull": "why you would or would not click, in a few words",
               "regret": "what would make you feel the click was wasted"}],
 "strongest_promise": 3, "why": "...",
 "weakest_promise": 5, "why_weakest": "..."}
```

`would_click`: at most three numbers, in the order you would click. `per_item`: one entry for every item on the shelf.
Then stop. Read no other file and write nothing else.
