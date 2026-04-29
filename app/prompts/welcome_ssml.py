WELCOME_SSML = """
<speak xmlns="http://www.w3.org/2001/10/synthesis"
       xmlns:mstts="http://www.w3.org/2001/mstts"
       version="1.0"
       xml:lang="en-US">
  <voice name="en-US-Aria:DragonHDLatestNeural">
    <mstts:express-as style="friendly" styledegree="1.0">
      <prosody rate="-6%" pitch="0%">
        Hello. <break time="220ms"/>
        Thanks for calling Stringham Consulting Services. <break time="260ms"/>
        My name is Ava. <break time="220ms"/>
        How can I help you today?
      </prosody>
    </mstts:express-as>
  </voice>
</speak>
""".strip()