ffmpeg -f lavfi -i "smptebars=duration=10:size=720x576:rate=25" \
       -f lavfi -i "sine=frequency=1000:duration=10" \
       -vf "setfield=tff,setdar=4/3" \
       -c:v v210 \
       -pix_fmt yuv422p10le \
       -r 25 \
       -c:a pcm_s16le \
       -ar 48000 \
       -ac 2 \
       -y \
       sd_pal_10bit_test.mov