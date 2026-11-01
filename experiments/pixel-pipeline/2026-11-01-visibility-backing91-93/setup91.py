from pathlib import Path
HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'eye-close90'
prefix=(OLD/'RUN_ReadAlpha90.cs.txt').read_text(encoding='utf-8').split('internal class CommandScript')[0]
source=(HERE/'ReadAlpha91.cs').read_text().replace('ROOT91',str(HERE))
(HERE/'RUN_ReadAlpha91.cs.txt').write_text(prefix+source[source.index('internal class CommandScript'):]+'\n}\n',encoding='utf-8')
relay=(OLD/'relay76.py').read_text();relay=relay.replace("'ReadAlpha90','FocusGPU90')", "'ReadAlpha90','FocusGPU90','ReadAlpha91')")
assert "'ReadAlpha91')"in relay
(HERE/'relay91.py').write_text(relay,encoding='utf-8')
print('Prepared bounded public-API reader; no Unity call.')
