"""Draw the canonical runtime plans, without inspecting or changing scene geometry."""
import json
import math
from pathlib import Path
import sys
from PIL import Image, ImageDraw, ImageFont

source = Path(sys.argv[1])
plans = json.loads(source.read_text(encoding="utf-8-sig"))["plans"]
if not plans:
    raise ValueError("No runtime floor plans were exported.")
max_floors = max(plan["floors"] for plan in plans)
columns = max_floors if max_floors > 1 else min(3, len(plans))
rows = len(plans) if max_floors > 1 else math.ceil(len(plans) / columns)
cell_width, cell_height = 650, 610
image = Image.new("RGB", (columns * cell_width + 30, rows * cell_height + 125), "#f3f0e8")
draw = ImageDraw.Draw(image)
font = ImageFont.truetype("C:/Windows/Fonts/malgun.ttf", 17)
title = ImageFont.truetype("C:/Windows/Fonts/malgunbd.ttf", 26)
names = {"supermarket": "마트", "police": "경찰서", "residential": "주거", "cafe": "카페", "retailshop": "소매점"}
room_names = {"Stockroom":"창고", "Staff room":"직원실", "WC":"화장실", "Service corridor":"직원\n통로",
              "Sales floor":"판매장", "Dining area":"접객·좌석", "Service counter":"주문\n카운터", "Kitchen":"주방"}
draw.text((30, 15), "실제 생성 데이터의 평면도", font=title, fill="#1c323b")
draw.text((30, 52), "정면(+Z)은 아래쪽  |  전체 도면의 미터당 축척은 동일  |  Mesh·Collider와 같은 설계 데이터", font=font, fill="#425b65")
scale = min(38, 530 / max(p["size"]["x"] for p in plans), 440 / max(p["size"]["y"] for p in plans))
for index, plan in enumerate(plans):
    for floor in range(plan["floors"]):
        row, column = (index, floor) if max_floors > 1 else (index // columns, index % columns)
        ox, oy = 30 + column*cell_width, 95 + row*cell_height
        w, d = plan["size"]["x"], plan["size"]["y"]
        left, top = ox+55+(530-w*scale)/2, oy+90
        def point(p): return (left+(p["x"]+w/2)*scale, top+(p["y"]+d/2)*scale)
        def rect(r):
            x,y=r["x"],r["y"]
            return (*point({"x":x,"y":y}),*point({"x":x+r["width"],"y":y+r["height"]}))
        draw.text((ox, oy), f'{names.get(plan["program"], plan["program"])}  {floor+1}층  /  {w:g} × {d:g}m', font=title, fill="#1c323b")
        draw.rectangle((left,top,left+w*scale,top+d*scale), fill="#fffdf6",outline="#314753",width=5)
        for room in plan["rooms"]:
            if room["floor"]!=floor: continue
            r=room["rect"]; box=rect(r)
            public=not room["hasDoor"]
            draw.rectangle(box,fill="#dcece3" if public else "#f5e6cc")
            words=room["role"].split(" ")
            label=room_names.get(room["role"], "\n".join(words) if len(words)>1 else words[0])
            cx=(box[0]+box[2])/2; cy=(box[1]+box[3])/2
            b=draw.multiline_textbbox((0,0),label,font=font,align="center")
            draw.multiline_text((cx-(b[2]-b[0])/2,cy-(b[3]-b[1])/2),label,font=font,fill="#42505a",align="center")
        if plan["floors"]>1 and plan["stair"]["width"]>0:
            box=rect(plan["stair"]);draw.rectangle(box,fill="#bcd7e2")
            for i in range(1,19):
                y=box[1]+(box[3]-box[1])*i/19
                draw.line((box[0],y,box[2],y),fill="#7398ab",width=1)
            a=point(plan["stairStart"]);b=point(plan["stairEnd"])
            draw.line((*a,*b),fill="#16547b",width=4)
            draw.polygon((b,(b[0]-9,b[1]+16),(b[0]+9,b[1]+16)),fill="#16547b")
        for wall in plan["walls"]:
            if wall["floor"]!=floor:continue
            a,b=point(wall["start"]),point(wall["end"])
            draw.line((*a,*b),fill="#314753",width=5)
            if wall["opening"]:
                c=point(wall["door"]);gap=wall["opening"]*scale/2
                segment=(c[0]-gap,c[1],c[0]+gap,c[1]) if abs(a[1]-b[1])<1 else (c[0],c[1]-gap,c[0],c[1]+gap)
                draw.line(segment,fill="#fffdf6",width=8)
        if floor==0:
            x=left+w*scale/2; y=top+d*scale
            draw.line((x-1.2*scale,y,x+1.2*scale,y),fill="#fffdf6",width=8)
            draw.text((x-32,y+9),"출입구",font=font,fill="#16547b")
            if plan.get("hasServiceDoor"):
                door = plan["serviceDoor"]
                x, y = point(door)
                gap = plan["serviceDoorWidth"] * scale / 2
                side = abs(abs(door["x"]) - w/2) < abs(abs(door["y"]) - d/2)
                segment = (x,y-gap,x,y+gap) if side else (x-gap,y,x+gap,y)
                draw.line(segment, fill="#fffdf6", width=8)
                outward = ((1 if door["x"]>0 else -1),0) if side else (0,(1 if door["y"]>0 else -1))
                end = (x+outward[0]*27,y+outward[1]*27)
                draw.line((x,y,*end),fill="#a45f28",width=3)
                if side:
                    draw.polygon((end,(end[0]-outward[0]*8,end[1]-5),(end[0]-outward[0]*8,end[1]+5)),fill="#a45f28")
                    label_position = (end[0]-25,end[1]-26)
                else:
                    draw.polygon((end,(end[0]-5,end[1]-outward[1]*8),(end[0]+5,end[1]-outward[1]*8)),fill="#a45f28")
                    label_position = (end[0]-36,end[1]-24 if outward[1]<0 else end[1]+5)
                draw.text(label_position,"서비스문",font=font,fill="#a45f28")
draw.text((30, image.height-30), "문 틈은 실제 통로 폭입니다. 설비·가구 표시는 생략하며 내부 역할과 동선을 나타냅니다.",font=font,fill="#425b65")
out = source.with_name("floorplans.png")
image.save(out)
print(out.resolve())
