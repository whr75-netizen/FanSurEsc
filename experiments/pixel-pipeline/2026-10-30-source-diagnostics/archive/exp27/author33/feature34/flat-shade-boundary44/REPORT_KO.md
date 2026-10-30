# 단색 명암 경계 후보 — 전체 정돈 미완

결론: 실제 Q 영역 마스크의 공유 경계부터 cubic 근사와 격자 재배치를 구현했고, 원래 팔레트로 출력했다. 최종 무회귀 후보는 **4셀 변경, 11→11영역, 단독6→6셀**이다. 전체가 깨끗해졌다는 결과가 아니다. 9개 공유 경로 중 1개만 실제 셀 변경까지 통과했다. `CURVES.json`, `LAYERS.npz`, `VERIFIED.json`이 대응 근거다.

## 6개 단독 셀의 원인

모든 g는 원본 측정 pool에서 확인됐고 Q 산술은 정확하다. 단색이므로 텍스처 색이나 RGB 팔레트가 이 Q 분단을 만든 것이 아니다. 현재 선택 packet의 실제 투영점 간 geometry를 다시 계산한 102개 Q 경계 중 같은 front chart39, 깊이 연속 owner교환5, 실제 앞뒤 가림55, 투영 빈틈3이다. 이 hair-only 분석이 face/body의 숨은 가림까지 증명하지는 않는다.

| 논리 좌표 | Q / 실제 g | 원래 중심→선택 Q | 인접 실제 가림/빈틈 변 | 같은 chart 내부 native Q 지원 |
|---|---|---|---:|---|
| [21, 9] | 2 / 0.05244904 | 2→2 | 1 | {'2': 2} |
| [23, 11] | 1 / 0.00888988 | 1→1 | 2 | {'1': 1} |
| [21, 14] | 3 / 0.06473462 | 3→3 | 3 | {'2': 2, '3': 1} |
| [8, 27] | 3 / 0.07102115 | 3→3 | 3 | {'2': 1} |
| [7, 29] | 2 / 0.02827420 | 3→2 | 1 | {'2': 2} |
| [7, 30] | 3 / 0.06662313 | 3→3 | 1 | {'3': 1} |

(7,29)는 표면 선택으로 g .06597649/Q3→.02827420/Q2가 되었다. 그 결과 예전 2셀 Q3 영역의 (7,30)도 단독이 된다. (7,30) 자체 g/Q는 바뀌지 않았다. 두 위치는 표본 선택의 분절 기여를 구체적으로 확인한 사례다. 다른 네 단독은 선택 이전에도 존재했다. 모두 '임계값 오류'나 '지워야 할 잡음'으로 분류하지 않았다. `SINGLETON_CAUSES.json`에는 각 셀의 이웃/실제 가림/표본/지원값이 있다.

## 실제 알고리즘과 확인한 실패

색이나 명암을 평균하지 않는다. Q의 두 라벨 사이 경계를 한 번만 만들고 두 면이 반대 방향으로 공동 사용한다. 마스크/접합 끝점은 고정한다. 깊이가 연속인 경우만 실제 g 교차점으로 guide를 잡고, 가림 변에서는 g를 섞지 않는다. coarse 격자의 계단 코너를 모두 원래 특징으로 고정하지 않았다. guide 근사→별도 4연결 격자 재배치→반대 winding에 의한 양쪽 라벨 채움→같은 P[Q'] 출력이다.

처음 곡선 재근사만 한 대조는 출력 변화0이었다. coarse 입력인데 native 간격의 작은 허용 오차로 계단까지 따라갔고, 연속 곡선을 셀 중심에서 판정하는 것만으로는 기존 raster를 바꾸지 못했다. 이 대조는 `fit-only-control-RESULTS.json`에 보존했다.

다음 무제약 곡선 raster는 (9,29)를 Q1→Q2로 바꿔 (8,29)의 유효 Q1 셀을 새로 고립시켰다. 단독6→7, 영역11→12의 **실패**다. 곡선 접선 오차가 줄었어도 채택하지 않았다. 원본/native g 지지가 있는 얇은 연결을 끊는 제안은 거부했다. 모든 기존 component/구멍을 무조건 동결하는 규칙은 넣지 않았다. 실패 PNG와 수치는 `unconstrained-failure-*`로 보존했다.

## 남긴 실제 변경

[
  {
    "index": 466,
    "xy": [
      18,
      14
    ],
    "beforeQ": 2,
    "afterQ": 3,
    "g": 0.042832452803850174,
    "sourceChart": 110002,
    "sourceWitnesses": [
      {
        "point": [
          18.499676509402065,
          13.499422973136191
        ],
        "g": 0.059819284826517105,
        "Q": 3,
        "chart": 110002,
        "primitive": 692,
        "visibility": "same front source chart throughout",
        "distanceOutsideCell": 0.5005770268638088
      }
    ],
    "pathId": 4,
    "addedGIntervalDistance": 0.012248993484809644,
    "beforeRGB8": [
      93,
      61,
      62
    ],
    "afterRGB8": [
      96,
      64,
      66
    ]
  },
  {
    "index": 497,
    "xy": [
      17,
      15
    ],
    "beforeQ": 3,
    "afterQ": 2,
    "g": 0.06922991573810577,
    "sourceChart": 120000,
    "sourceWitnesses": [
      {
        "point": [
          17.500809445020536,
          16.50059566908233
        ],
        "g": 0.04280832037329674,
        "Q": 2,
        "chart": 120000,
        "primitive": 51,
        "visibility": "same front source chart throughout",
        "distanceOutsideCell": 0.5005956690823297
      }
    ],
    "pathId": 4,
    "addedGIntervalDistance": 0.014148469449445956,
    "beforeRGB8": [
      96,
      64,
      66
    ],
    "afterRGB8": [
      93,
      61,
      62
    ]
  },
  {
    "index": 527,
    "xy": [
      15,
      16
    ],
    "beforeQ": 2,
    "afterQ": 3,
    "g": 0.05170615762472153,
    "sourceChart": 110004,
    "sourceWitnesses": [
      {
        "point": [
          15.500062578022806,
          15.49992856748112
        ],
        "g": 0.06073911860585213,
        "Q": 3,
        "chart": 110004,
        "primitive": 1023,
        "visibility": "same front source chart throughout",
        "distanceOutsideCell": 0.5000714325188795
      },
      {
        "point": [
          15.499978788929013,
          16.000182722348896
        ],
        "g": 0.056891970336437225,
        "Q": 3,
        "chart": 110004,
        "primitive": 1025,
        "visibility": "same front source chart throughout",
        "distanceOutsideCell": 0.0
      },
      {
        "point": [
          15.999639013181962,
          16.00027843787948
        ],
        "g": 0.062296703457832336,
        "Q": 3,
        "chart": 110004,
        "primitive": 1025,
        "visibility": "same front source chart throughout",
        "distanceOutsideCell": 0.0
      },
      {
        "point": [
          15.999879988813888,
          16.500165822683925
        ],
        "g": 0.05728638544678688,
        "Q": 3,
        "chart": 110004,
        "primitive": 1027,
        "visibility": "same front source chart throughout",
        "distanceOutsideCell": 0.0
      }
    ],
    "pathId": 4,
    "addedGIntervalDistance": 0.0033752886639382904,
    "beforeRGB8": [
      93,
      61,
      62
    ],
    "afterRGB8": [
      96,
      64,
      66
    ]
  },
  {
    "index": 682,
    "xy": [
      10,
      21
    ],
    "beforeQ": 3,
    "afterQ": 2,
    "g": 0.05772460624575615,
    "sourceChart": 120006,
    "sourceWitnesses": [
      {
        "point": [
          11.000411447323074,
          20.499857143517183
        ],
        "g": 0.05282687395811081,
        "Q": 2,
        "chart": 120006,
        "primitive": 1019,
        "visibility": "same front source chart throughout",
        "distanceOutsideCell": 0.5001430257233342
      },
      {
        "point": [
          11.000598224669261,
          20.99965043977442
        ],
        "g": 0.05165843665599823,
        "Q": 2,
        "chart": 120006,
        "primitive": 1019,
        "visibility": "same front source chart throughout",
        "distanceOutsideCell": 0.0006928673078012883
      },
      {
        "point": [
          11.500369801788537,
          20.999791819476172
        ],
        "g": 0.04551975056529045,
        "Q": 2,
        "chart": 120006,
        "primitive": 1083,
        "visibility": "same front source chart throughout",
        "distanceOutsideCell": 0.5003698450956355
      },
      {
        "point": [
          11.000568770787822,
          21.49987433850336
        ],
        "g": 0.04734154790639877,
        "Q": 2,
        "chart": 120006,
        "primitive": 1084,
        "visibility": "same front source chart throughout",
        "distanceOutsideCell": 0.0005687707878223591
      },
      {
        "point": [
          11.50025605925515,
          21.500048754117742
        ],
        "g": 0.041316643357276917,
        "Q": 2,
        "chart": 120006,
        "primitive": 1084,
        "visibility": "same front source chart throughout",
        "distanceOutsideCell": 0.5002560592551504
      },
      {
        "point": [
          11.00046004348846,
          22.00023570726809
        ],
        "g": 0.04500972479581833,
        "Q": 2,
        "chart": 120006,
        "primitive": 1084,
        "visibility": "same front source chart throughout",
        "distanceOutsideCell": 0.0005169119146470445
      },
      {
        "point": [
          11.500186257166831,
          22.000404136816215
        ],
        "g": 0.03796270489692688,
        "Q": 2,
        "chart": 120006,
        "primitive": 1085,
        "visibility": "same front source chart throughout",
        "distanceOutsideCell": 0.5001864204325519
      },
      {
        "point": [
          10.5000148985647,
          22.49983330690852
        ],
        "g": 0.04480625316500664,
        "Q": 2,
        "chart": 120006,
        "primitive": 1023,
        "visibility": "same front source chart throughout",
        "distanceOutsideCell": 0.49983330690852057
      },
      {
        "point": [
          10.999970950664903,
          22.49996674361558
        ],
        "g": 0.043420206755399704,
        "Q": 2,
        "chart": 120006,
        "primitive": 1086,
        "visibility": "same front source chart throughout",
        "distanceOutsideCell": 0.49996674361558036
      }
    ],
    "pathId": 4,
    "addedGIntervalDistance": 0.002643159957096332,
    "beforeRGB8": [
      96,
      64,
      66
    ],
    "afterRGB8": [
      93,
      61,
      62
    ]
  }
]

이 변경 경로의 고정 reference arclength 접선 오차는 0.203877925506724→0.17180815111879805다. 위치/라벨/원래g 오차도 함께 기록했고, 둘레 감소만을 성공 기준으로 쓰지 않았다. original Q와 g는 불변이며 Q'는 별도다.

긴 Q2/Q3 경로는 처음에 source 지지를 '기존 셀 내부'에서만 찾는 제약에 막혔다. 그러나 (18,14)의 같은 chart110002에서 셀 바깥0.500577칸에 실제 Q3/g=.05981928 표본이 있고 그 사이 가림이 없음을 확인했다. 움직일 경계를 기존 coarse 칸으로 동결한 것이 과도했다. 선언한 같은 공간 보정 범위 안에서 실제 동일 표면의 지지를 쓰도록 고쳐 긴 경로의4셀 재배치를 검사했다. 다른 표면/색을 평균하거나 임계값을 바꾼 것이 아니다. 모든 witness 거리/가림/원래g 대비 오차를 공개했다.

그 밖의 6경로는 이번 공간 오차 범위에서 셀을 바꾸지 않았다. 한 경로는 source-constrained 격자 접합이 모호하여 제외했고, 얇은 연결을 끊던 경로도 제외했다. 즉 완성된 전두부 정돈이나 6개 섬 제거 결과가 아니며, 단색에서도 실제 표면 가림·선택점·명암 분포가 남는 병목이다. 원래6셀 모두를 잡음이라고 증명하지 않았다.

## 보존·검증·한계

원래 source/g/Q/geometry/P/카메라/2×2와 마스크 밖 RGBA를 보존했다. 모든 final hair RGB는 P[Q']에 정확히 속한다. 간격 m=0/.5/1/1.5는 기존 palette API로 색만 바꾸며 Q/Q'/곡선은 고정했다. 역순 제안과 출력이 같고 실제 PNG를 검수했다. 11개 추적 제품/템플릿 hash 변화0. Unity 호출·추가 캡처·Desktop/31/34/제품 변경0이며 현재 Editor/dirty를 새로 조회하지 않았다. 실제 움직임은 미검증이다.

이 후보를 더 강하게 만든다고 임의 오차나 면적 목표를 높이지 않았다. 남은 얇은 명암과 가림을 어느 정도 단순화할지의 판단 없이 기존 측정 g 특징을 일괄 삭제한 결과로 보고하지 않는다. 그래도 영역 보정 자체가 불가능하다는 뜻은 아니다. 이번 구현/반례/실제 변경은 명시적으로 분리된, 제한된 정지 프레임 결과다.


직접 PNG 검수와 run 진행은 [VISUAL_REVIEW_KO.md](VISUAL_REVIEW_KO.md) 및 [DIRECTION_FLOW.json](DIRECTION_FLOW.json)에 기록했다. 가림/표본/Q 원인 분리는 했지만 g의 normal/direct/shadow 항별 기여까지 전부 분해하지 않았다.
