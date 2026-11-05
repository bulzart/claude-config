# Verified 2026-09-16 on ffmpeg 9.0.1 (Gyan full build), Windows PowerShell 5.1.
# Renders two sample clips to 9:16 1080x1920 30fps H.264 High + AAC with: cover-fit scale/crop,
# xfade slideleft, setpts/atempo speed change on clip 2, ASS captions (libass, optional fontsdir),
# SFX via adelay+amix, loudnorm to -14 LUFS, faststart. Took ~4.2 s for 5 s of output.
$env:Path = [Environment]::GetEnvironmentVariable('Path','Machine') + ';' + [Environment]::GetEnvironmentVariable('Path','User')
$ff  = 'C:\Users\Bulzart\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffmpeg.exe'
$fp  = 'C:\Users\Bulzart\AppData\Local\Microsoft\WinGet\Packages\Gyan.FFmpeg_Microsoft.Winget.Source_8wekyb3d8bbwe\ffmpeg-9.0.1-full_build\bin\ffprobe.exe'
$c1  = 'C:\Users\Bulzart\.claude\analyze-stack\samples\generated-clips\clip-02-seg-0-15.mp4'
$c2  = 'C:\Users\Bulzart\.claude\analyze-stack\samples\generated-clips\clip-03-seg-15-30.mp4'
$out = "$PSScriptRoot\smoke.mp4"
$sfx = "$PSScriptRoot\sfx.wav"
# ASS path for the filter graph: forward slashes and escaped drive colon (C\:)
$ass = ("$PSScriptRoot\captions-karaoke-sample.ass" -replace '\\', '/') -replace ':', '\:'
# Optional: folder with un-installed TTFs (Montserrat, Anton ...) -> fontsdir
$fd  = ('C:/Users/Bulzart/.claude/analyze-stack/tools/edit/fonts') -replace ':', '\:'
$assFilter = "ass='$ass'"
if (Test-Path 'C:\Users\Bulzart\.claude\analyze-stack\tools\edit\fonts') { $assFilter = "ass='$ass':fontsdir='$fd'" }

# 0.25 s test SFX
& $ff -y -hide_banner -loglevel error -f lavfi -i 'sine=frequency=880:duration=0.25' -af 'afade=t=out:st=0.1:d=0.15' $sfx

$fc = "[0:v]trim=0:3,setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p[v0];" +
      "[1:v]trim=0:3,setpts=PTS-STARTPTS,scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920,fps=30,format=yuv420p,setpts=0.8*PTS[v1];" +
      "[v0][v1]xfade=transition=slideleft:duration=0.4:offset=2.6[vx];" +
      "[vx]$assFilter[vout];" +
      "[0:a]atrim=0:3,asetpts=PTS-STARTPTS[a0];[1:a]atrim=0:3,asetpts=PTS-STARTPTS,atempo=1.25[a1];" +
      "[a0][a1]acrossfade=d=0.4[amain];[2:a]adelay=2600|2600,volume=0.6[asfx];" +
      "[amain][asfx]amix=inputs=2:duration=first:normalize=0[amix];[amix]loudnorm=I=-14:TP=-1.5:LRA=11[aout]"

& $ff -y -hide_banner -loglevel error -stats -i $c1 -i $c2 -i $sfx -filter_complex $fc -map '[vout]' -map '[aout]' `
  -c:v libx264 -profile:v high -level 4.1 -preset medium -crf 18 -pix_fmt yuv420p -r 30 -g 60 `
  -c:a aac -b:a 192k -ar 48000 -movflags +faststart $out

& $fp -v error -show_entries stream=codec_type,codec_name,profile,width,height,r_frame_rate,pix_fmt,sample_rate,channels:format=duration,size -of compact $out
# Frame grabs (ffmpeg 9 needs -update 1 for a single image)
& $ff -y -hide_banner -loglevel error -ss 1.0 -i $out -frames:v 1 -update 1 "$PSScriptRoot\frame_1s.png"
& $ff -y -hide_banner -loglevel error -ss 2.8 -i $out -frames:v 1 -update 1 "$PSScriptRoot\frame_2p8s.png"
# Two-pass loudnorm measurement (feed these into measured_I/measured_TP/measured_LRA/measured_thresh/offset)
& $ff -hide_banner -i $out -af 'loudnorm=I=-14:TP=-1.5:LRA=11:print_format=json' -f null NUL 2>&1 | Select-String -Pattern 'input_i|input_tp|input_lra|input_thresh|target_offset' | ForEach-Object { $_.Line.Trim() }
