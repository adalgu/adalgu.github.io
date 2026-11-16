---
title: "I Built a 216-Song Commute Playlist by Chatting with an AI Browser"
description: "How I handed the YouTube Music work to an AI browser and built a 216-song commute playlist through conversation alone, plus what I learned along the way."
draft: false
translationKey: "ai-browser-commute-playlist"
url: "/en/posts/ai-browser-commute-playlist/"
date: 2026-11-09T00:07:00+09:00
slug: ai-browser-commute-playlist
tags: ["AI", "music", "automation"]
cover:
  image: "cover.jpg"
  alt: "Illustration of a phone in a car mount showing a music playlist, inside a car driving on a highway on an autumn morning"
  relative: true
  hiddenInSingle: false
  hiddenInList: false
---
Once I passed forty, the music I listened to in the car on my commute started to sound the same every day. I still love the high-note ballads and hip-hop I used to sing at noraebang (노래방, Korean karaoke rooms) in my twenties and thirties, and I'm willing to practice newer songs if I need to. The problem was that deciding what to listen to, finding it, and adding it to a playlist one song at a time was a hassle.

So this time I handed the process over to an **AI browser**. This isn't a chatbot that just suggests song titles. It opens YouTube Music in the browser where I'm already logged in, reads my existing playlists, searches for songs, adds them to a new playlist, and even checks the result.

The result was a **216-song commute playlist**. What was more interesting than the result, though, was the process. I described my taste as if I were chatting, and the AI browser carried it through into actual work on the web, which made picking songs feel far more free.

## The difference between chatbot recommendations and an AI browser

A typical AI recommendation usually ends here.

> “If you like songs like these, give the following a listen.” (“이런 노래를 좋아하시면 다음 곡을 들어보세요.”)

After that, it's back on me. I have to search for each song on YouTube Music, check the artist and version, add it to a playlist, and make sure nothing got left out.

The AI browser picked up that middle part and handled it.

| Step | Typical chatbot recommendation | How it went with the AI browser |
|---|---|---|
| Understanding my taste | I describe the songs I like myself | It reads my YouTube Music playlists directly |
| Recommending | Mostly just song titles | YouTube links and the reason for each pick included |
| Applying feedback | Reflected only in the conversation | Applied right away to the next round's selection criteria |
| Saving | The user searches and adds songs one by one | It searches and adds them directly in the YouTube Music interface |
| Verifying | The user checks separately | It checks the actual playlist screen and the song count |
| Using it | The recommendation list is kept somewhere separate | It even puts together a shuffle-play link |

The key is that **recommendation and execution were never separated**. When I said “let's drop this one” (“이 곡은 빼자”) or “let's add more songs by this artist” (“이 가수 곡을 더 넣자”) mid-conversation, that decision turned straight into work on the web.

## 1. It read my taste from my existing playlists

I didn't start by writing a long description of my taste. I had the AI browser read two playlists I had already made on YouTube Music.

- **korea list**: 262 songs
- **Good List (좋은리스트)**: 86 songs

{{< figure src="01-original-list.jpg" link="01-original-list.jpg" alt="YouTube Music playlist screen. On the left, the title Good List and 86 tracks; on the right, the song list. The account name is blurred" caption="My existing playlist, Good List (86 songs). Account name blurred" >}}

What the two lists had in common was pretty clear.

- **High-note ballads** from the likes of SG Wannabe (SG워너비), M.C the Max (엠씨더맥스), Park Hyo-shin (박효신), and Gummy (거미)
- **Melodic hip-hop** from the likes of Epik High (에픽하이), Dynamic Duo (다이나믹 듀오), and MC Sniper (MC 스나이퍼)
- **Idol and band music** from the likes of BIGBANG (빅뱅), 2NE1, and DAY6

The AI browser started its recommendations by avoiding songs that were already in there where possible and looking for new songs in a similar vein. I didn't have to copy and paste the lists myself.

## 2. I narrowed down my taste ten songs at a time

I didn't take a hundred recommendations all at once. I got them **ten at a time**, and I just replied with the numbers of the songs I liked or didn't.

For each song, the AI browser found a listening link on YouTube and attached it, along with a short explanation of why it was recommended. Because I could listen right away and decide, choosing felt like less of a burden.

{{< figure src="05-aside-round1.jpg" link="05-aside-round1.jpg" alt="AI browser chat screen. My request at the top, below it the 10-song list for round 1 with a YouTube link and reason for each, and at the bottom confirmed so far 0/100" caption="Round 1 recommendations. Each song came with a YouTube link and a reason" >}}

| Round | My reaction | What changed in the next recommendations |
|---|---|---|
| 1 | Picked 9 of 10. I know Epik High's ‘One’, but I'm not a fan | Kept Epik High, but recommended songs with a different mood |
| 2 | Picked all 10 | Kept the mix of high-note ballads, emotional hip-hop, and band songs |
| 3 | Dropped QWER. Gave feedback that the artists overlapped too much | Excluded QWER entirely, stronger artist rotation |
| 4 | Picked all 10 | Widened the range to Kim Kyung-ho (김경호), The Cross (더 크로스), Zico (지코), N.Flying (엔플라잉), and others |

In particular, the recommendations changed dramatically after one remark: “the artists keep overlapping” (“가수가 계속 겹친다”). Instead of the same artists repeating, a variety of artists took turns, which made the list less tedious for commuting.

{{< figure src="06-aside-feedback-rotation.jpg" link="06-aside-feedback-rotation.jpg" alt="AI browser chat screen. At the top, my request to drop QWER and rotate artists; below it, the 10-song artist-rotation list for round 4 and confirmed so far 27/100" caption="Round 4 recommendations, after I said the artists keep overlapping" >}}

## 3. I mixed in pop at only about 1.5 songs per 10

In round 5, I tried mixing in three pop songs. I mentioned that I sometimes sing ‘I Left My Heart in San Francisco’ at noraebang, and since I don't know much about jazz, it took that into account and started me off with easygoing standard pop.

- Frank Sinatra, **Fly Me to the Moon**
- Oasis, **Don’t Look Back in Anger**
- Bruno Mars, **When I Was Your Man**

I liked all three, but I preferred pop to come up only now and then. So from then on we settled on **an average of 1.5 songs per 10**, alternating between one and two.

Adjusting a ratio like this took just one line of conversation. I didn't need to explain the recommendation rules again or reorganize the list myself.

## 4. I slipped in songs as they came to mind

As I went through the recommendations, songs I had loved long ago kept coming to mind. I mentioned those as they came up.

- Vasco (바스코)'s **First Feeling (첫느낌)**
- Brown Eyes (브라운 아이즈)'s **FOR YOU (돌아가줘)**
- The One (더원)'s **Someday (썸데이)** and **It Passes By (지나간다)**
- Nami (나미)'s **You, Whom I Want to Be Close To (가까이 하고 싶은 그대)**

There turned out to be several hip-hop songs titled ‘First Feeling’. The AI browser found the candidates and showed them to me, and it added the song after I confirmed it was the Vasco one. That confirmation step helped keep the wrong songs from getting in.

{{< figure src="02-search-song.jpg" link="02-search-song.jpg" alt="YouTube Music search screen. The search box reads 첫느낌 힙합, and below it are several songs with the same title" caption="Search results for ‘첫느낌 힙합’ (First Feeling hip-hop). Several songs share the title" >}}

## 5. I grew it from 100 songs to 216

After finishing round 10, I had 99 songs. The original goal was 100, but I figured it would be nice to have more to listen to, so from then on **I raised the batch size to around 20 songs.**

| Stage | Result |
|---|---|
| After round 10 | 99 songs |
| 21 more songs recommended | 120 songs |
| Dropped 2 of 20 | 138 songs |
| Dropped 1 of 20 | 157 songs |
| Picked all 20 | 177 songs |
| Dropped 1 of 20 | 196 songs |
| Added city pop and songs by favorite artists | 216 songs |

The songs I dropped meant something too. I liked Baechigi (배치기)'s ‘Maidongpung’ (‘마이동풍’), but ‘Two Mari’ (‘두 마리’) wasn't for me. I learned that rather than liking or disliking an artist wholesale, **my taste splits song by song**.

Partway through, I also got 20 city pop recommendations and picked just some of them.

- Miki Matsubara (마츠바라 미키), **Stay With Me**
- Mariya Takeuchi (타케우치 마리야), **Plastic Love**
- Kiyotaka Sugiyama & Omega Tribe (스기야마 키요타카 & 오메가 트라이브), **SUMMER SUSPICION**
- Kim Hyun-chul (김현철), **What's Wrong (왜 그래)**
- YUKIKA (유키카), **Soul Lady (서울여자)**

After that, I also added songs by favorite artists.

- **Lee Seung-chul (이승철):** Jasmine Flower (말리꽃), Destiny (인연), Shout (소리쳐), Western Sky (서쪽 하늘), No One Else (그런 사람 또 없습니다)
- **Kim Gun-mo (김건모):** Beautiful Farewell (아름다운 이별), Moon of Seoul (서울의 달), I'm Sorry (미안해요), Excuse (핑계), Sleepless Night, Rain Is Falling (잠 못 드는 밤 비는 내리고), The Way I Look (내 모습을), Sadder Today Than Yesterday (어제보다 슬픈 오늘), To You (너에게)
- **Flower (플라워):** Endless, Tears (눈물), Expression of Affection (애정표현)

## 6. It didn't stop at recommending; it built the actual playlist

Once the song selection was done, the AI browser created a new private playlist on YouTube Music. Then it searched for each song, checked the artist and version, and added it to the playlist.

{{< figure src="03-save-to-playlist.jpg" link="03-save-to-playlist.jpg" alt="YouTube Music Save to playlist dialog. Under Recent, the 216-song commute playlist is shown; other playlists are blurred" caption="The save-to-playlist dialog (captured after all 216 songs were in). Other playlists blurred" >}}

Adding hundreds of songs at once also taught me an important lesson. At first I assumed every song I'd picked had gone in, but when I actually checked, only some of them had been saved. After that we added them in several batches, yet even when the “saved” notification appeared, some songs were missing from the actual list.

{{< figure src="07-aside-honest-status.jpg" link="07-aside-honest-status.jpg" alt="AI browser chat screen. A report that only 4 songs were actually in the playlist and the remaining 198 had not been added yet, alongside that playlist screen" caption="A progress report that stated the actual number of songs saved" >}}

In the end, the AI browser reopened the actual playlist, checked the song count, cross-checked for the missing songs, and filled them in. It would have been quite a chore if a person had to compare everything one by one at the end.

{{< figure src="04-final-playlist.jpg" link="04-final-playlist.jpg" alt="YouTube Music playlist screen. Commute playlist, private, 216 tracks, with the song list. The account name is blurred" caption="The finished commute playlist (216 songs)" >}}

The lesson here is clear.

> When you hand web work to an AI, don't stop at its report that it “added them” (“추가했다”); include a step that checks the actual screen and the resulting numbers.

The advantage of the AI browser was that it could handle this verification within the same flow.

## 7. Shuffle play with a single link

A YouTube Music playlist URL usually looks like this (재생목록ID stands for the playlist ID).

```text
https://music.youtube.com/playlist?list=재생목록ID
```

Change `playlist` to `watch` and append `&shuffle=1`, and you can use it as a shuffle-play link.

```text
https://music.youtube.com/watch?list=재생목록ID&shuffle=1
```

Now on my way to work, all I have to do is tap this one link. That said, it isn't a URL option documented in YouTube Music's official help, so it may behave differently depending on the app or browser environment. If it doesn't shuffle automatically, just tap **Shuffle** in the playlist menu.

If the playlist is private, it only opens when you're logged in to the same account. To share the link with blog readers, I'd need to change the playlist to unlisted.

## Things to try next

What struck me most while doing this was that with an AI browser, making a playlist stops being a one-off task and can become **a personal music assistant you keep reshaping over time**.

### Seasonal playlists

The mood of a commute changes with each season.

- **Spring:** bright band songs, fresh acoustic tracks
- **Summer:** city pop, dance tracks for driving
- **Fall:** lyrical ballads, mellow R&B
- **Winter:** high-note ballads, warm OST tracks

I could make seasonal sub-lists based on the existing 216 songs, or mix in new recommendations to make a version for each season.

### A list for trips with the kids

When I'm in the car with my kids, it's hard to insist on only my own taste. I can put together a good mix of songs the kids like, songs we can all sing along to, and Korean and Western pop that isn't too heavy.

For example, I could ask something like this.

> “Make a two-hour family road trip playlist that's 70% the 2000s songs Dad likes and 30% upbeat songs the kids can sing along to.” (“아빠가 좋아하는 2000년대 노래 70%, 아이들이 따라 부를 수 있는 신나는 곡 30%로 2시간짜리 가족 여행 플레이리스트를 만들어 줘.”)

The AI browser can draw on my existing playlists and current hits to come up with candidates, then add only the ones I pick to an actual playlist.

### A Jeju Island trip theme

A playlist tailored to a destination, like Korea's Jeju Island, sounds fun too.

- City pop for driving along the coastal road
- Acoustic songs to listen to while looking at the sea
- Bright songs to sing together with the kids
- Quiet ballads for relaxing at the place we're staying

If I tell it the destination, who's coming along, the travel time, and the mood, it can make a separate travel list to match.

### Mixing in new releases a little at a time

I like familiar songs, but I'd also like to practice a few newer ones to sing at noraebang. Going forward, I can keep my existing taste while mixing in a new release or two at a time.

> “Keep the mood of my playlist, but mix in high-note noraebang songs released in the past year, at only about 1 in every 10.” (“내 플레이리스트 분위기는 유지하되, 최근 1년 안에 나온 노래방용 고음곡을 10곡당 1곡 정도만 섞어 줘.”)

Doing it this way, I can learn new songs without the playlist suddenly turning into something unfamiliar.

### Updating it regularly

Instead of leaving a finished list as it is, I can also update it regularly.

- Get a few new-release candidates recommended every month
- Remove the songs I often skip and find similar replacements
- Add new songs to the candidates when a favorite artist releases something
- Make new playlists to fit the season or my schedule

Of course, for actions that leave a lasting result, like actually adding songs or changing the visibility setting, it's better to confirm before going ahead. Even so, the AI browser can take a lot of the repetitive work out of finding, comparing, and organizing candidates.

## Wrapping up

What mattered in this playlist project wasn't only that the AI knows music well. It mattered a lot that, in the YouTube Music interface I actually use, it read my existing playlists, changed its criteria through conversation, searched for songs, added them to a playlist, and checked the result.

Making a playlist used to take time spent searching and clicking myself. Now I just say “let's drop this one,” “just a little pop” (“팝은 조금만 넣자”), or “let's add more songs by this artist.” The AI browser turns those words into actual work on the web.

So these 216 songs are closer to a beginning than an end. I plan to revise the list when the seasons change, make a new one before a family trip, and mix in new releases a little at a time.

Musical taste keeps changing. And now, reflecting that change in a playlist can feel as natural as having a conversation.
