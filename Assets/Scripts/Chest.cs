using UnityEngine;
using VariableInventorySystem; // ★ 에셋 네임스페이스 사용

// 이 스크립트를 상자 프리팹 또는 게임 오브젝트에 추가하세요.
// 상자 오브젝트에는 Collider 컴포넌트가 있어야 하고, IsTrigger가 체크되어 있어야 합니다.
// 또한, 플레이어의 OnTriggerEnter/Exit에서 감지할 수 있도록 적절한 레이어("Chest" 등) 또는 태그("Chest" 등)를 설정해야 합니다.
public class Chest : MonoBehaviour
{
    public StandardStashViewData chestInventoryData; // 이 상자만의 고유 인벤토리 데이터

    [Tooltip("이 상자 인벤토리의 가로 칸 수")]
    public int chestWidth = 6; // 상자마다 다르게 설정 가능
    [Tooltip("이 상자 인벤토리의 세로 칸 수")]
    public int chestHeight = 5; // 상자마다 다르게 설정 가능

    void Awake()
    {
        // 이 상자를 위한 인벤토리 데이터 초기화
        chestInventoryData = new StandardStashViewData(chestWidth, chestHeight);

        // 필요하다면 여기에 이 상자의 초기 아이템을 추가하는 코드를 넣으세요.
        // 예시:
        // var item = new ItemCellData(0); // ItemCellData는 직접 만드신 아이템 데이터 클래스여야 합니다.
        // int? id = chestInventoryData.GetInsertableId(item);
        // if (id.HasValue)
        // {
        //     chestInventoryData.InsertInventoryItem(id.Value, item);
        // }
    }
}