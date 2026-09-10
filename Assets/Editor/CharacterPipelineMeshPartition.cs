using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Rendering;

namespace FantasySurvival.EditorTools
{
    /// <summary>Editor-only skin-weight partitioning; callers own and must destroy returned meshes.</summary>
    public static class CharacterPipelineMeshPartition
    {
        /// <summary>
        /// Copies the source mesh and retains triangles belonging to the requested bone group.
        /// A bone belongs to its nearest ancestor (including itself) in groupBones. Triangle
        /// ownership uses all three vertices' summed weights; ties choose the lowest group index.
        /// Vertex data, skinning, blend shapes and material-slot/submesh order remain intact.
        /// Must run in Edit Mode, which can read imported meshes without changing Read/Write.
        /// This does not bake a pose, alter the renderer, or change its shared mesh or materials.
        /// </summary>
        public static Mesh ExtractGroup(SkinnedMeshRenderer source, Transform[] groupBones, int requestedGroup)
        {
            if (Application.isPlaying)
                throw new InvalidOperationException("Partition meshes must be prepared in Edit Mode before entering Play Mode.");
            if (source == null)
                throw new ArgumentNullException(nameof(source));
            if (groupBones == null)
                throw new ArgumentNullException(nameof(groupBones));
            if (groupBones.Length == 0)
                throw new ArgumentException("At least one bone group is required.", nameof(groupBones));
            if (requestedGroup < 0 || requestedGroup >= groupBones.Length)
                throw new ArgumentOutOfRangeException(nameof(requestedGroup));

            Mesh sourceMesh = source.sharedMesh;
            if (sourceMesh == null)
                throw new ArgumentException("The renderer has no shared mesh.", nameof(source));

            var groupIndices = new Dictionary<Transform, int>(groupBones.Length);
            for (int group = 0; group < groupBones.Length; group++)
            {
                Transform groupBone = groupBones[group];
                if (groupBone == null)
                    throw new ArgumentException($"Bone group {group} is null.", nameof(groupBones));
                if (groupIndices.ContainsKey(groupBone))
                    throw new ArgumentException($"Bone '{groupBone.name}' is listed more than once.", nameof(groupBones));
                groupIndices.Add(groupBone, group);
            }

            Transform[] sourceBones = source.bones;
            var boneGroups = new int[sourceBones.Length];
            for (int bone = 0; bone < sourceBones.Length; bone++)
            {
                boneGroups[bone] = -1;
                for (Transform ancestor = sourceBones[bone]; ancestor != null; ancestor = ancestor.parent)
                {
                    if (!groupIndices.TryGetValue(ancestor, out int group))
                        continue;
                    boneGroups[bone] = group;
                    break;
                }
            }

            double[,] vertexWeights = ReadVertexGroupWeights(sourceMesh, sourceBones, boneGroups, groupBones.Length);
            var retainedBySubmesh = new List<int>[sourceMesh.subMeshCount];
            var baseVertices = new int[sourceMesh.subMeshCount];
            for (int submesh = 0; submesh < sourceMesh.subMeshCount; submesh++)
            {
                if (sourceMesh.GetTopology(submesh) != MeshTopology.Triangles)
                    throw new InvalidOperationException($"Submesh {submesh} does not use triangle topology.");

                int[] triangles = sourceMesh.GetTriangles(submesh, false);
                if (triangles.Length % 3 != 0)
                    throw new InvalidOperationException($"Submesh {submesh} has an incomplete triangle.");
                int baseVertex = checked((int)sourceMesh.GetBaseVertex(submesh));
                baseVertices[submesh] = baseVertex;
                var retained = new List<int>();
                retainedBySubmesh[submesh] = retained;
                for (int index = 0; index < triangles.Length; index += 3)
                {
                    int first = checked(triangles[index] + baseVertex);
                    int second = checked(triangles[index + 1] + baseVertex);
                    int third = checked(triangles[index + 2] + baseVertex);
                    if (first < 0 || first >= sourceMesh.vertexCount ||
                        second < 0 || second >= sourceMesh.vertexCount ||
                        third < 0 || third >= sourceMesh.vertexCount)
                        throw new InvalidOperationException($"Submesh {submesh} contains an invalid vertex index.");

                    int winner = -1;
                    double largestWeight = 0d;
                    for (int group = 0; group < groupBones.Length; group++)
                    {
                        double weight = vertexWeights[first, group] + vertexWeights[second, group] +
                            vertexWeights[third, group];
                        // Strictly greater preserves the lowest group index on an exact tie.
                        if (weight <= largestWeight)
                            continue;
                        largestWeight = weight;
                        winner = group;
                    }
                    if (winner < 0)
                        throw new InvalidOperationException($"Submesh {submesh}, triangle {index / 3} has no positive bone weights.");
                    if (winner != requestedGroup)
                        continue;

                    retained.Add(triangles[index]);
                    retained.Add(triangles[index + 1]);
                    retained.Add(triangles[index + 2]);
                }
            }

            // Instantiate would inherit a non-readable imported mesh's write restrictions.
            // Build an owned, readable mesh from data read in Edit Mode instead.
            var result = new Mesh();
            try
            {
                result.name = $"{sourceMesh.name}_Group{requestedGroup}_{groupBones[requestedGroup].name}";
                CopyVertexData(sourceMesh, result);
                result.subMeshCount = sourceMesh.subMeshCount;
                for (int submesh = 0; submesh < result.subMeshCount; submesh++)
                {
                    // Retain empty submeshes so the original sharedMaterials mapping still applies.
                    result.SetTriangles(retainedBySubmesh[submesh], submesh, false, baseVertices[submesh]);
                }
                result.bounds = sourceMesh.bounds;
                return result;
            }
            catch
            {
                UnityEngine.Object.DestroyImmediate(result);
                throw;
            }
        }

        private static void CopyVertexData(Mesh source, Mesh destination)
        {
            destination.indexFormat = source.indexFormat;
            destination.vertices = source.vertices;
            if (source.HasVertexAttribute(VertexAttribute.Normal))
                destination.normals = source.normals;
            if (source.HasVertexAttribute(VertexAttribute.Tangent))
                destination.tangents = source.tangents;
            if (source.HasVertexAttribute(VertexAttribute.Color))
            {
                if (source.GetVertexAttributeFormat(VertexAttribute.Color) == VertexAttributeFormat.UNorm8)
                    destination.colors32 = source.colors32;
                else
                    destination.colors = source.colors;
            }

            for (int channel = 0; channel < 8; channel++)
            {
                var attribute = (VertexAttribute)((int)VertexAttribute.TexCoord0 + channel);
                if (!source.HasVertexAttribute(attribute))
                    continue;
                int dimension = source.GetVertexAttributeDimension(attribute);
                switch (dimension)
                {
                    case 2:
                        var uv2 = new List<Vector2>();
                        source.GetUVs(channel, uv2);
                        destination.SetUVs(channel, uv2);
                        break;
                    case 3:
                        var uv3 = new List<Vector3>();
                        source.GetUVs(channel, uv3);
                        destination.SetUVs(channel, uv3);
                        break;
                    case 4:
                        var uv4 = new List<Vector4>();
                        source.GetUVs(channel, uv4);
                        destination.SetUVs(channel, uv4);
                        break;
                    default:
                        throw new InvalidOperationException($"UV channel {channel} has unsupported dimension {dimension}.");
                }
            }

            destination.bindposes = source.bindposes;
            // Source-owned Allocator.None views are read synchronously and must not be disposed.
            destination.SetBoneWeights(source.GetBonesPerVertex(), source.GetAllBoneWeights());

            if (source.blendShapeCount == 0)
                return;
            var deltaVertices = new Vector3[source.vertexCount];
            var deltaNormals = new Vector3[source.vertexCount];
            var deltaTangents = new Vector3[source.vertexCount];
            for (int shape = 0; shape < source.blendShapeCount; shape++)
            {
                string shapeName = source.GetBlendShapeName(shape);
                for (int frame = 0; frame < source.GetBlendShapeFrameCount(shape); frame++)
                {
                    source.GetBlendShapeFrameVertices(shape, frame, deltaVertices, deltaNormals, deltaTangents);
                    destination.AddBlendShapeFrame(shapeName, source.GetBlendShapeFrameWeight(shape, frame),
                        deltaVertices, deltaNormals, deltaTangents);
                }
            }
        }

        private static double[,] ReadVertexGroupWeights(Mesh mesh, Transform[] sourceBones, int[] boneGroups, int groupCount)
        {
            var groupWeights = new double[mesh.vertexCount, groupCount];
            // These are read-only Allocator.None views owned by Mesh, not caller allocations.
            // Do not Dispose them or retain them beyond this synchronous read of the source.
            var bonesPerVertex = mesh.GetBonesPerVertex();
            var allWeights = mesh.GetAllBoneWeights();
            if (bonesPerVertex.Length != mesh.vertexCount)
                throw new InvalidOperationException($"Mesh '{mesh.name}' has no complete per-vertex skinning data.");

            int weightIndex = 0;
            for (int vertex = 0; vertex < mesh.vertexCount; vertex++)
            {
                int count = bonesPerVertex[vertex];
                if (count > allWeights.Length - weightIndex)
                    throw new InvalidOperationException($"Mesh '{mesh.name}' has incomplete bone weights at vertex {vertex}.");
                for (int influence = 0; influence < count; influence++)
                {
                    BoneWeight1 weight = allWeights[weightIndex++];
                    if (float.IsNaN(weight.weight) || float.IsInfinity(weight.weight) || weight.weight < 0f)
                        throw new InvalidOperationException($"Vertex {vertex} has an invalid bone weight.");
                    if (weight.weight == 0f)
                        continue;
                    if (weight.boneIndex < 0 || weight.boneIndex >= boneGroups.Length)
                        throw new InvalidOperationException($"Vertex {vertex} references missing bone index {weight.boneIndex}.");

                    int group = boneGroups[weight.boneIndex];
                    if (group < 0)
                    {
                        Transform bone = sourceBones[weight.boneIndex];
                        string boneName = bone != null ? bone.name : "<null>";
                        throw new InvalidOperationException($"Vertex {vertex}, bone {weight.boneIndex} '{boneName}' has no ancestor in groupBones.");
                    }
                    groupWeights[vertex, group] += weight.weight;
                }
            }
            if (weightIndex != allWeights.Length)
                throw new InvalidOperationException($"Mesh '{mesh.name}' has unaccounted bone weights.");
            return groupWeights;
        }
    }
}
