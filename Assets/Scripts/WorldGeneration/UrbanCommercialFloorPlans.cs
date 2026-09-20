using System;
using System.Collections.Generic;
using UnityEngine;

namespace FantasySurvival.WorldGeneration
{
    /// <summary>
    /// Commercial program partitions in the existing local XZ metre frame. These are game-scale
    /// modules, not copied construction drawings or a building-code certification. Physical props
    /// retain their authored size; wider footprints enlarge public/storage rooms rather than doors.
    /// </summary>
    internal static class UrbanCommercialFloorPlans
    {
        private const float InteriorInset = .2f, RoomDoorWidth = 1.6f, CorridorWidth = 1.8f;

        public static UrbanFloorPlan Build(int buildingIndex, UrbanArchitectureProgram program, Vector2 size)
        {
            if (!float.IsFinite(size.x) || !float.IsFinite(size.y) || size.x < 12f || size.y < 10f)
                throw new ArgumentException("Commercial modules require an unscaled footprint at least 12m x 10m.", nameof(size));
            var rooms = new List<UrbanPlanRoom>();
            var walls = new List<UrbanPlanPartition>();
            float left = -size.x * .5f + InteriorInset, right = size.x * .5f - InteriorInset;
            float back = -size.y * .5f + InteriorInset, front = size.y * .5f - InteriorInset;
            Vector2 serviceDoor = default;

            switch (program)
            {
                case UrbanArchitectureProgram.Supermarket:
                    Supermarket();
                    break;
                case UrbanArchitectureProgram.Cafe:
                    Cafe();
                    break;
                case UrbanArchitectureProgram.RetailShop:
                    RetailShop();
                    break;
                default:
                    throw new ArgumentException("The program is not a commercial module.", nameof(program));
            }
            return new UrbanFloorPlan(buildingIndex, program, size, rooms, walls, null, new List<Rect>(), serviceDoor);

            void Supermarket()
            {
                // A transverse service hall separates sales from independent support rooms.
                float roomFront = back + 3.2f, hallFront = roomFront + CorridorWidth;
                OpenRoom("Sales floor", Rect.MinMaxRect(left, hallFront, right, front));
                OpenRoom("Service corridor", Rect.MinMaxRect(left, roomFront, right, hallFront));
                HorizontalWall(left, right, hallFront, 0f, CorridorWidth);
                float staffLeft = right - 5.6f, wcLeft = right - 2.8f;
                RearRoom("Stockroom", left, staffLeft, roomFront);
                RearRoom("Staff room", staffLeft, wcLeft, roomFront);
                RearRoom("WC", wcLeft, right, roomFront);
                SolidVertical(staffLeft, back, roomFront);
                SolidVertical(wcLeft, back, roomFront);
                serviceDoor = new Vector2((left + staffLeft) * .5f, -size.y * .5f);
            }

            void Cafe()
            {
                // Open dining and barista zones face one another. The rear hall provides WC access
                // without sending customers through food preparation, stock or staff rooms.
                float roomFront = back + 3.2f, hallFront = roomFront + CorridorWidth;
                float counterLeft = right - 3f;
                OpenRoom("Dining area", Rect.MinMaxRect(left, hallFront, counterLeft, front));
                OpenRoom("Service counter", Rect.MinMaxRect(counterLeft, hallFront, right, front));
                OpenRoom("Service corridor", Rect.MinMaxRect(left, roomFront, right, hallFront));
                HorizontalWall(left, counterLeft, hallFront, 0f, CorridorWidth);
                HorizontalWall(counterLeft, right, hallFront, (counterLeft + right) * .5f, RoomDoorWidth);
                float stockLeft = right - 7.2f, staffLeft = right - 4.8f, wcLeft = right - 2.4f;
                RearRoom("Kitchen", left, stockLeft, roomFront);
                RearRoom("Stockroom", stockLeft, staffLeft, roomFront);
                RearRoom("Staff room", staffLeft, wcLeft, roomFront);
                RearRoom("WC", wcLeft, right, roomFront);
                SolidVertical(stockLeft, back, roomFront);
                SolidVertical(staffLeft, back, roomFront);
                SolidVertical(wcLeft, back, roomFront);
                serviceDoor = new Vector2((left + stockLeft) * .5f, -size.y * .5f);
            }

            void RetailShop()
            {
                // A longitudinal staff/service route branches to stock on its left and two rooms
                // on its right. Its topology differs from the supermarket's transverse rear band.
                float serviceFront = back + 5.2f, split = back + 2.6f;
                float corridorRight = right - 3.2f, corridorLeft = corridorRight - CorridorWidth;
                OpenRoom("Sales floor", Rect.MinMaxRect(left, serviceFront, right, front));
                OpenRoom("Service corridor", Rect.MinMaxRect(corridorLeft, back, corridorRight, serviceFront));
                Room("Stockroom", Rect.MinMaxRect(left, back, corridorLeft, serviceFront),
                    new Vector2(corridorLeft, split));
                Room("Staff room", Rect.MinMaxRect(corridorRight, back, right, split),
                    new Vector2(corridorRight, (back + split) * .5f));
                Room("WC", Rect.MinMaxRect(corridorRight, split, right, serviceFront),
                    new Vector2(corridorRight, (split + serviceFront) * .5f));
                VerticalWall(corridorLeft, back, serviceFront, split);
                VerticalWall(corridorRight, back, split, (back + split) * .5f);
                VerticalWall(corridorRight, split, serviceFront, (split + serviceFront) * .5f);
                HorizontalWall(corridorRight, right, split);
                HorizontalWall(left, corridorLeft, serviceFront);
                HorizontalWall(corridorRight, right, serviceFront);
                // The 1.8m open end of the side corridor connects directly to the sales floor.
                serviceDoor = new Vector2((left + corridorLeft) * .5f, -size.y * .5f);
            }

            void OpenRoom(string role, Rect bounds) => rooms.Add(new UrbanPlanRoom(0, role, bounds));
            void Room(string role, Rect bounds, Vector2 door) => rooms.Add(new UrbanPlanRoom(0, role, bounds, true, door));
            void RearRoom(string role, float x0, float x1, float z)
            {
                float x = (x0 + x1) * .5f;
                Room(role, Rect.MinMaxRect(x0, back, x1, z), new Vector2(x, z));
                HorizontalWall(x0, x1, z, x, RoomDoorWidth);
            }
            void HorizontalWall(float x0, float x1, float z, float doorX = 0f, float opening = 0f) =>
                walls.Add(new UrbanPlanPartition(0, new Vector2(x0, z), new Vector2(x1, z), new Vector2(doorX, z), opening));
            void SolidVertical(float x, float z0, float z1) =>
                walls.Add(new UrbanPlanPartition(0, new Vector2(x, z0), new Vector2(x, z1)));
            void VerticalWall(float x, float z0, float z1, float doorZ) =>
                walls.Add(new UrbanPlanPartition(0, new Vector2(x, z0), new Vector2(x, z1), new Vector2(x, doorZ), RoomDoorWidth));
        }
    }
}
