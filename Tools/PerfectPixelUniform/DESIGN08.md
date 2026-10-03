# V8 — 목재 재료의 2단계 제한을 4단계 명암으로 수정

사용자 정정: 나뭇결을2색으로만표현해명암/입체감이부족하므로참고작을찾고최소3~4색을사용한다. 직접원인은woodpalette4개를보유해도grain.npy가bool이고pixel index=band+grain이라한면안에서최대2색이되는입력표현이다. geometry/AA/해상도오류와혼동하지않는다.

기준자료는[imonk의원문](https://itch.io/t/1452767/pixel-tutorial-wood-texture):물결형평행결·타원옹이·추가갈색단계,선을따라이어지는명암,무작위색/급격한끊김으로벌레먹거나파인인상을주는반례. [Rappenem의단계별그림](https://www.newgrounds.com/art/view/rappenem/pixel-art-tutorial-wood-texture)과[Pixel Pete강좌](https://www.youtube.com/watch?v=nzzphDLsO8g)도참고링크로보존하나후자의영상기법을자막없이검증했다고주장하지않는다. 원문자산을게임재료로복사하지않는다.

## 고정 연산

생성목재source/ROI/원본RGB4표본/128×54 UV grid/물리period는유지한다. V7평판구조·camera·nativecanvas·그림자band·외곽선과비목재RGBA는그대로다. 새생성·Blender재계산·기하보정·퍼펙트픽셀·축소·디더링은제외한다. 실제PNG의목재내부만source팔레트색으로재제작한다.

ROI 원래sRGB밝기값 `.2126R+.7152G+.0722B`의p10/p25/p75를고정분류경계로쓰고각texel은이전과같은source중앙한점을조회한다. `L>=p75`는밝은결0,`p25<=L<p75`는중간1,`p10<=L<p25`는어두운결2,`L<p10`은깊은옹이/골3이다. 역할이공간적으로의미있는모든옹이를정확히인식했다는뜻은아니며관측명암분류다.

각nesteddarkmask `L<p75`, `L<p25`, `L<p10`에서이전과같은8연결6texel미만독립성분을제외한다. 포함관계를검사하고세mask합으로0..3을구한다. 작은밝은0성분도6미만이면중간1로병합한다. 위치를랜덤생성하거나모든결에두꺼운하이라이트테두리를추가하지않는다. 명시적재료저작의손실수는기록하고원본특징전부보존을주장하지않는다.

기존surface UV/원본생성palettes/기하band/ink를읽어 wood의index를`min(structuralBand+materialLevel,3)`로선택한다. top의band0에는실제4색이모두남아야한다. 기존visibleink는항상기존RGBA를유지하며wood밖픽셀도byte동일하다. nativePNG크기와RGBAalpha를그대로유지한다. 그림자를재료명암으로대체하지않는다.

## 마지막 판별

graph-v8은tone-map→pixels→validate3노드다. material/raster를한장씩판단하면서반복보정하지않는다. sourceRGBA/oldgeometry코드·배열·sceneSHA보존,목재제외RGBA와ink불변,alpha불변,top내부4색각6px이상/4sourceRGB만사용,정수4배·같은canvas,UV레벨유효/nested확인,실제source견본RGB출처를최종저장출력에서한번확인한다. 색수충족이미술승인이나참고작자동재현은아니다.

## 실제 결과

3노드1회실행완료,geometry재실행/생성/시각재보정없음. UV4level은1556/3820/1025/511texel이다. nested어두운3mask에서작은성분은2/101/100개(5/255/241texel)제거,작은bright0성분92개/195texel을중간1로합병했다. 원화의미세명암을영역저작한명시적손실이며원본특징완전보존은아니다.

상판내부에서4source목재RGB각각2칸1000/2006/686/222px,3칸1332/3012/876/414px를관측했다. 두native152×150/192×170/alpha는V7과동일하고nonwood/ink RGBA가byte동일하다. V7기하/관련소스SHA그대로이며geometry를복제·재계산하지않았다. material계산.112초,3노드process포함약1.37초는설계·조사·AI작업시간과별개다. 결과/검사/실행기록은Parametric08에보존했다. 미술승인/범용재료자동인식/Unity표시는미검증이다.

별도 읽기 전용 agent도 실제 PNG/NPZ/source 견본을 대조하여 alpha/nonwood/ink 변경0px와 상판4RGB 개수 및 source 중앙표본 동일을 확인했다. 미술성공 판정은 하지 않았다. 직접 최종검사는47조건을 통과했다.
