using UnityEngine;
using UnityEngine.SceneManagement;
using VariableInventorySystem;

namespace FantasySurvival.Inventory
{
    public interface IWorldItemDropReceipt : IVariableInventoryExternalDropReceipt
    {
        WorldItemPickup Pickup { get; }
        InventoryItemData Item { get; }
    }

    public interface IWorldItemDropService
    {
        bool TryStage(
            InventoryItemData detachedItem,
            out IWorldItemDropReceipt receipt,
            out string error);
    }

    /// <summary>
    /// Creates a scene-local test representation for one detached runtime item.
    /// The provisional sphere stays inactive until the inventory core commits the
    /// source release, so a creation failure can still use the existing rollback.
    /// </summary>
    public sealed class WorldItemDropService : IWorldItemDropService
    {
        private const float DefaultDropDistance = 0.9f;
        private const float DefaultSphereDiameter = 0.32f;
        private const float GroundProbeHeight = 2.5f;
        private const float GroundProbeDistance = 8f;

        private readonly Transform dropOrigin;

        public WorldItemDropService(Transform dropOrigin)
        {
            this.dropOrigin = dropOrigin;
        }

        public bool TryStage(
            InventoryItemData detachedItem,
            out IWorldItemDropReceipt receipt,
            out string error)
        {
            receipt = null;
            if (dropOrigin == null)
            {
                error = "바닥 아이템을 놓을 Player 위치가 없습니다.";
                return false;
            }

            if (detachedItem == null || detachedItem.InventoryOwner != null)
            {
                error = "바닥 드롭은 원본에서 정상 분리된 아이템만 처리할 수 있습니다.";
                return false;
            }

            Vector3 position = ResolveDropPosition();
            GameObject sphere = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            sphere.SetActive(false);
            sphere.transform.position = position;
            sphere.transform.localScale = Vector3.one * DefaultSphereDiameter;

            Scene activeScene = SceneManager.GetActiveScene();
            if (activeScene.IsValid() && activeScene.isLoaded &&
                sphere.scene != activeScene)
            {
                SceneManager.MoveGameObjectToScene(sphere, activeScene);
            }

            WorldItemPickup pickup = sphere.AddComponent<WorldItemPickup>();
            if (!pickup.TryInitialize(detachedItem, out error))
            {
                DestroyObject(sphere);
                return false;
            }

            receipt = new Receipt(pickup, detachedItem, pickup.Inventory);
            error = null;
            return true;
        }

        private Vector3 ResolveDropPosition()
        {
            Vector3 forward = Vector3.ProjectOnPlane(dropOrigin.forward, Vector3.up);
            if (forward.sqrMagnitude < 0.001f)
            {
                forward = Vector3.forward;
            }
            else
            {
                forward.Normalize();
            }

            Vector3 target = dropOrigin.position + forward * DefaultDropDistance;
            Vector3 probeOrigin = target + Vector3.up * GroundProbeHeight;
            if (Physics.Raycast(
                    probeOrigin,
                    Vector3.down,
                    out RaycastHit hit,
                    GroundProbeDistance,
                    Physics.AllLayers,
                    QueryTriggerInteraction.Ignore))
            {
                target = hit.point;
            }

            target.y += DefaultSphereDiameter * 0.5f;
            return target;
        }

        private static void DestroyObject(GameObject target)
        {
            if (target == null)
            {
                return;
            }

            if (Application.isPlaying)
            {
                Object.Destroy(target);
            }
            else
            {
                Object.DestroyImmediate(target);
            }
        }

        private sealed class Receipt : IWorldItemDropReceipt
        {
            private enum ReceiptState
            {
                Pending,
                Committed,
                RolledBack
            }

            private readonly StandardStashViewData provisionalOwner;
            private ReceiptState state;

            public Receipt(
                WorldItemPickup pickup,
                InventoryItemData item,
                StandardStashViewData provisionalOwner)
            {
                Pickup = pickup;
                Item = item;
                this.provisionalOwner = provisionalOwner;
            }

            public WorldItemPickup Pickup { get; }
            public InventoryItemData Item { get; }

            public bool TryCommit(out string error)
            {
                if (state == ReceiptState.Committed)
                {
                    error = null;
                    return true;
                }

                if (state != ReceiptState.Pending)
                {
                    error = "이미 원복된 바닥 드롭은 확정할 수 없습니다.";
                    return false;
                }

                if (Pickup == null || provisionalOwner == null || Item == null ||
                    !ReferenceEquals(Item.InventoryOwner, provisionalOwner) ||
                    !provisionalOwner.GetId(Item).HasValue)
                {
                    error = "확정할 임시 바닥 아이템의 소유권 또는 오브젝트가 없습니다.";
                    return false;
                }

                try
                {
                    Pickup.gameObject.SetActive(true);
                }
                catch (System.Exception exception)
                {
                    error = $"바닥 아이템 표시를 확정하지 못했습니다: {exception.Message}";
                    return false;
                }

                state = ReceiptState.Committed;
                error = null;
                return true;
            }

            public bool TryRollback(out string error)
            {
                if (state == ReceiptState.RolledBack)
                {
                    error = null;
                    return true;
                }

                if (state == ReceiptState.Committed)
                {
                    error = "이미 확정된 바닥 드롭은 원복할 수 없습니다.";
                    return false;
                }

                if (provisionalOwner == null || Item == null)
                {
                    error = "임시 바닥 아이템의 논리 소유권 정보가 없습니다.";
                    return false;
                }

                if (ReferenceEquals(Item.InventoryOwner, provisionalOwner))
                {
                    int? slot = provisionalOwner.GetId(Item);
                    if (!slot.HasValue)
                    {
                        error = "임시 바닥 아이템의 논리 슬롯을 찾을 수 없습니다.";
                        return false;
                    }

                    try
                    {
                        provisionalOwner.InsertInventoryItem(slot.Value, null);
                    }
                    catch (System.Exception exception)
                    {
                        error = $"임시 바닥 아이템 분리에 실패했습니다: {exception.Message}";
                        return false;
                    }
                }
                else if (Item.InventoryOwner != null)
                {
                    error = "임시 바닥 아이템이 알 수 없는 소유자로 이동해 원복할 수 없습니다.";
                    return false;
                }

                state = ReceiptState.RolledBack;
                if (Pickup != null)
                {
                    DestroyObject(Pickup.gameObject);
                }
                error = null;
                return true;
            }
        }
    }
}
