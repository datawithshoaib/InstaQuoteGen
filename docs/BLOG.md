# I rebuilt my AI quote generator, and the first thing I found was my own API keys

I run a small Instagram page that posts quotes. A while back I built a tool to make those posts
for me: type a topic, get a quote from an AI model, drop it on a nice photo, download the image.
It worked. I used it. I didn't look at the code very closely after that.

This month I finally sat down to clean it up, and it turned into a full rebuild. This post is about
what I found, what I changed, and what I learned about building something with AI in it that you
can actually trust.

## The embarrassing part first

The backend served images to the frontend using a static file folder. Except I had pointed that
folder at the root of the project, not at the images. So if you went to
`/static/assets/.env` you could download the file with my API keys in it.

There was also an endpoint that let the website update those keys. It had no login, and the
server accepted requests from any website. So in theory any page I visited could have swapped my
keys for its own.

Nobody exploited it as far as I know. It ran on my laptop. But it's exactly the kind of thing that
ends up on a server one day "just for a quick demo". The fix was small: only serve the two folders
that hold images, delete the key endpoint, and read keys from the environment. I also wrote a test
that tries to download `.env` and fails if it works. That test will outlive my memory of this bug.

## The "AI pipeline" was mostly a dictionary

The old version said it used a multi-step LangGraph workflow. It did have three steps. The first
one looked up your topic in a hard-coded list of related words. The second called the model. The
third tidied up hashtags. So really it was one prompt with some decoration around it.

That one prompt also had no quality control. Whatever came back went straight into my quote
library: clichés, near-copies of famous quotes, lines that didn't fit the topic. And the model was
asked to name an author, which means it would happily attribute made-up quotes to real people. I
did not want my page doing that.

## What the new pipeline does

I kept LangGraph, but now every step earns its place:

1. **Plan.** The model suggests a few specific angles on the topic. "Discipline" might become
   "discipline when nobody is watching" and "discipline in small daily habits". This alone made
   the quotes less samey.
2. **Write.** The model drafts the quotes, plus one spare. It gets told which quotes already exist
   so it doesn't repeat them.
3. **Review.** This is the part I'm happiest with. First some plain rules that cost nothing: is it
   between 5 and 28 words, does it contain hashtags or emoji, does it use a phrase like "never give
   up", is it too close to a quote I already have. Whatever survives goes to a second model call
   that acts as a strict editor and scores each quote out of 10 on originality, clarity, impact
   and fit.
4. **Rewrite if needed.** If not enough quotes pass, the rejected ones and the editor's notes go
   back to the writer for another try. That happens at most twice, so a bad day can't loop forever.
5. **Finish.** Keep the best ones and clean up the hashtags.

AI-written quotes never get an author now. If you want an author, you type it yourself.

## Making the AI part boring in a good way

A few small decisions made the whole thing much more predictable.

**The model has to fill in a form.** Every call to the model asks for a specific structure (a
list of quotes, each with text, keywords and hashtags) and the answer is checked against it. If
the model returns something malformed, that's an error I can see, not a half-broken quote on my
page.

**Prompts have a version number.** Every run records which version of the prompts it used. When
quality changes I can see whether it lines up with a prompt edit.

**Every run is recorded.** For each generation I store how long each step took, how many tokens it
used, how many drafts were rejected and why, and the final scores. There's a Runs page in the app
that shows all of this. It sounds like overkill for a quote generator, but it's the only way to
answer "did that change make things better?" without guessing.

**It fails gracefully.** No API key, the provider is down, or the run takes more than 90 seconds:
in all of those cases you still get quotes, pulled from the saved library, and the app tells you
that's what happened instead of pretending.

**There's a fake model for testing.** I wrote a stand-in that behaves like the real one but always
gives the same answers, and it deliberately slips in one cliché so the review step has something
to reject. The test suite runs the whole pipeline with it in under a minute, with no internet and
no API costs. There's also a small evaluation script that runs ten sample topics and reports
average scores, how often drafts pass, and how varied the results are. I can run it before and
after a prompt change and compare.

## Watching it think

My favourite part of the new frontend is the Generate page. While the pipeline runs, the backend
streams each step to the browser as it happens. You see Plan light up, then Write, then Review,
and below that a log of every draft the editor looked at: the keepers with their scores, the
rejects crossed out with the reason. "Uses a cliché ('believe in yourself')." It's oddly
satisfying.

It's also useful. When a run gives weak results I can see why straight away, instead of rerunning
it and hoping.

## Making the posts look better

The old renderer wrapped text by counting characters, so big fonts ran off the edge of the image.
Now it measures the actual pixel width, and it balances the lines so you don't get one lonely word
on the last line. The font shrinks automatically if the quote is long. I swapped the hard black
outline around the text for a soft shadow, and added a gold opening quote mark.

The studio preview in the browser uses the same font and the same layout rules as the image
renderer, so what you see while editing is what you get when you export. Photos come from Unsplash
and the photographer is credited in the caption, which I should have been doing from the start.

## Things that went wrong during the rebuild

Not everything worked first time.

- The fallback gradient backgrounds had a visible rectangle in them. I only noticed because I
  rendered all six colour themes side by side and looked.
- The headline gradient on the home page showed up as solid coloured boxes in the browser. It
  needed the old `-webkit-` version of a CSS property.
- The animated glowing background was so heavy that the browser froze on my laptop. I had used
  three giant blurred shapes. I replaced them with plain gradients that look identical and cost
  almost nothing.

The lesson from all three: look at the thing. Tests passing doesn't tell you a gradient has a
seam in it.

## What I'd tell myself a year ago

- Read your own code before you trust it. The scariest bug here was one line long.
- An AI feature isn't one prompt. It's the checks around the prompt that make it reliable.
- Cheap rules first, expensive model calls second.
- Write down what happened on every run. You'll want that history the first time quality drops.
- Build a fake version of the model early. It makes testing free and fast, and it lets you work on
  the UI without burning through API credits.

The code is all in the repo, and there's a phase-by-phase write-up in `docs/PHASES.md` if you want
the details. Next on my list is running the evaluation against the real model to get a proper
baseline, then trying a few prompt tweaks and seeing whether the numbers agree with my gut.
