using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using FantasySurvival.CharacterPresentation;
using FantasySurvival.CharacterPresentation.ModularSprites;
using FantasySurvival.Rendering;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;
using UnityEngine.SceneManagement;
using Object = UnityEngine.Object;

namespace FantasySurvival.EditorTools
{
    /// <summary>
    /// A bounded, isolated pipeline proof. Only newly created comparison assets are written.
    /// B is an automatic walk bake; C derives fixed front cutouts + 2D poses from the same rig.
    /// It does not invent back views, regenerate game objects, or modify approved shaders.
    /// </summary>
    public static class CharacterPipelineComparisonBuilder
    {
        public const string Root = "Assets/Tests/CharacterPipelines/Review01";
        public const string ScenePath = Root + "/CharacterPipelineComparison.unity";
        public const int Width = 256, Height = 512, FrameCount = 16, Ppu = 96;
        public const float Duration = 4f / 3f;
        private const string Evidence = "LocalOnly/CharacterPipelineComparison_20260910";
        private const string Source = "Assets/Prefabs/PersistentGameplayShell.prefab";
        private static Action stopBake;
        private static readonly HumanBodyBones[] Groups = {
            HumanBodyBones.Hips, HumanBodyBones.Head,
            HumanBodyBones.LeftUpperArm, HumanBodyBones.LeftLowerArm, HumanBodyBones.LeftHand,
            HumanBodyBones.RightUpperArm, HumanBodyBones.RightLowerArm, HumanBodyBones.RightHand,
            HumanBodyBones.LeftUpperLeg, HumanBodyBones.LeftLowerLeg, HumanBodyBones.LeftFoot,
            HumanBodyBones.RightUpperLeg, HumanBodyBones.RightLowerLeg, HumanBodyBones.RightFoot };
        private static readonly int[] Parents = { -1, 0, 0, 2, 3, 0, 5, 6, 0, 8, 9, 0, 11, 12 };

        [Serializable] public sealed class BakeRecord
        {
            public string status;
            public int width = Width, height = Height, frames = FrameCount, ppu = Ppu;
            public string[] partIds;
            public Vector2[] pivots;
            public Vector2Int[] bindPositions;
            public int[] layerOrder;
            public ModularSpriteMotionFrame[] poses;
            public string source = Source;
        }

        [MenuItem("Tools/Fantasy Survival/Character Presentation/Open Pipeline Comparison")]
        public static void OpenComparison()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode) return;
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            if (!File.Exists(ScenePath)) throw new InvalidOperationException("Comparison has not been built yet.");
            EditorSceneManager.OpenScene(ScenePath);
        }

        public static void Prepare()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode)
                throw new InvalidOperationException("Prepare requires Edit Mode.");
            for (int i = 0; i < SceneManager.sceneCount; i++)
                if (SceneManager.GetSceneAt(i).isDirty)
                    throw new InvalidOperationException("An open scene has unsaved changes; no scenes changed.");
            if (AssetDatabase.IsValidFolder(Root))
                throw new InvalidOperationException("Review01 already exists. Existing review is never overwritten automatically.");
            EnsureFolder(Root);
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var source = AssetDatabase.LoadAssetAtPath<GameObject>(Source).transform.Find("Player/CharacterSilhouettePlayerVisual");
            var live = Object.Instantiate(source.gameObject);
            live.name = "A_Live3D_PresentationOnly";
            live.transform.position = Vector3.zero;
            live.transform.rotation = Quaternion.identity;
            var demo = new GameObject("Pipeline Comparison - NOT Gameplay").AddComponent<CharacterPipelineComparison>();
            demo.liveAnimator = live.GetComponentInChildren<Animator>();
            demo.cycleSeconds = Duration;
            demo.animate = false;
            var camera = new GameObject("Comparison Camera").AddComponent<Camera>();
            camera.tag = "MainCamera";
            camera.orthographic = true;
            camera.orthographicSize = Height / (2f * Ppu);
            camera.transform.SetPositionAndRotation(new Vector3(0, 1.7f, 14), Quaternion.Euler(0, 180, 0));
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(.13f, .15f, .18f, 0);
            camera.allowHDR = false; camera.allowMSAA = false;
            var extra = camera.GetUniversalAdditionalCameraData();
            extra.renderPostProcessing = false; extra.antialiasing = AntialiasingMode.None;
            var key = MakeLight("Review Key", 2f, new Vector3(30,205,0));
            MakeLight("Review Fill", .55f, new Vector3(5,140,0));
            demo.keyLight = key;
            RenderSettings.sun = key;
            RenderSettings.ambientMode = AmbientMode.Flat;
            RenderSettings.ambientLight = Color.white * .3f;
            RenderSettings.fog = false;
            EditorSceneManager.SaveScene(scene, ScenePath);
            Selection.activeGameObject = demo.gameObject;
            Debug.Log("Prepared isolated comparison scene. Enter Play Mode, then BeginBake(). Existing gameplay assets unchanged.");
        }

        public static void BeginBake()
        {
            if (!EditorApplication.isPlaying || SceneManager.GetActiveScene().path != ScenePath)
                throw new InvalidOperationException("Bake requires the isolated comparison scene in Play Mode.");
            if (stopBake != null) throw new InvalidOperationException("A bake is already active.");
            var demo = Object.FindFirstObjectByType<CharacterPipelineComparison>();
            demo.animate = false; demo.enabled = false; demo.Sample(0);
            var animator = demo.liveAnimator;
            var subject = animator.GetComponentInParent<CharacterSilhouetteSubject>();
            var camera = Camera.main;
            var feature = AssetDatabase.LoadAssetAtPath<UniversalRendererData>("Assets/Settings/PC_Renderer.asset")
                .rendererFeatures.OfType<CharacterSilhouetteRendererFeature>().Single();
            var renderers = subject.GetComponentsInChildren<SkinnedMeshRenderer>();
            var originals = renderers.Select(r => r.sharedMesh).ToArray();
            var previousForce = renderers.Select(r => r.forceMatrixRecalculationPerRender).ToArray();
            var groups = Groups.Select(animator.GetBoneTransform).ToArray();
            if (groups.Any(t => t == null)) throw new InvalidOperationException("Missing required humanoid bone.");
            var partitions = new Mesh[Groups.Length][];
            var record = new BakeRecord {
                partIds = Groups.Select(g=>g.ToString()).ToArray(), pivots = new Vector2[Groups.Length],
                bindPositions = new Vector2Int[Groups.Length], poses = new ModularSpriteMotionFrame[FrameCount]
            };
            Directory.CreateDirectory(Evidence);
            var target = new RenderTexture(Width, Height, 24, RenderTextureFormat.ARGB32) { filterMode = FilterMode.Point, antiAliasing = 1 };
            var image = new Texture2D(Width, Height, TextureFormat.RGBA32, false);
            var oldTarget = camera.targetTexture;
            float oldAspect = camera.aspect;
            bool oldCamera = camera.enabled;
            bool oldBackground = Application.runInBackground;
            var bindAngles = new float[Groups.Length];
            int cursor = 0, lastFrame = -1;
            double started = EditorApplication.timeSinceStartup;
            EditorApplication.CallbackFunction update = null;
            Action<PlayModeStateChange> onPlay = null;
            AssemblyReloadEvents.AssemblyReloadCallback onReload = null;
            Action<string> finish = null;
            finish = status => {
                if (stopBake == null) return;
                stopBake = null;
                EditorApplication.update -= update;
                EditorApplication.playModeStateChanged -= onPlay;
                AssemblyReloadEvents.beforeAssemblyReload -= onReload;
                for (int r=0;r<renderers.Length;r++) if(renderers[r]!=null) {
                    renderers[r].sharedMesh = originals[r];
                    renderers[r].forceMatrixRecalculationPerRender = previousForce[r];
                }
                // Partitions are editor-generated assets, not runtime-owned allocations.
                if(camera!=null) {camera.targetTexture=oldTarget; camera.aspect=oldAspect; camera.enabled=oldCamera;}
                feature.ResetAdaptiveToneHistory(camera);
                target.Release(); Object.DestroyImmediate(target); Object.DestroyImmediate(image);
                Application.runInBackground = oldBackground;
                if(demo!=null) demo.enabled = true;
                record.status = status;
                File.WriteAllText(Evidence+"/bake.json",JsonUtility.ToJson(record,true));
                Debug.Log("Character comparison bake: "+status+", samples="+cursor+", output="+Evidence);
            };
            stopBake = () => finish("cancelled");
            onPlay = s => {if(s==PlayModeStateChange.ExitingPlayMode) finish("Play Mode exited");};
            onReload = () => finish("assembly reload");
            try {
                target.Create(); camera.targetTexture=target; camera.aspect=(float)Width/Height; camera.enabled=false;
                Application.runInBackground=true;
                foreach(var r in renderers) r.forceMatrixRecalculationPerRender=true;
                var prepared = AssetDatabase.LoadAllAssetsAtPath(Root+"/Editor/BakePartitions.asset")
                    .OfType<Mesh>().ToDictionary(m=>m.name);
                for(int g=0;g<groups.Length;g++) {
                    // Unity names the MAIN mesh after its asset file on import; subasset names stay intact.
                    partitions[g] = Enumerable.Range(0,renderers.Length).Select(r=>g==0&&r==0
                        ? AssetDatabase.LoadAssetAtPath<Mesh>(Root+"/Editor/BakePartitions.asset")
                        : prepared["group_"+g+"_renderer_"+r]).ToArray();
                    var v = camera.WorldToViewportPoint(groups[g].position);
                    record.pivots[g] = new Vector2(v.x,v.y);
                    record.bindPositions[g] = Project(groups[g].position,camera);
                    bindAngles[g] = BoneAngle(groups,g,camera,animator);
                }
                // Every source triangle must belong to exactly one part, not duplicated by overlapping boxes.
                for(int r=0;r<renderers.Length;r++) {
                    long before=0,after=0;
                    for(int s=0;s<originals[r].subMeshCount;s++) before+=originals[r].GetIndexCount(s);
                    foreach(var row in partitions) for(int s=0;s<row[r].subMeshCount;s++) after+=row[r].GetIndexCount(s);
                    if(before!=after) throw new InvalidOperationException("Partition lost/duplicated triangles: "+renderers[r].name);
                }
                record.layerOrder = Enumerable.Range(0,groups.Length)
                    .OrderByDescending(g=>camera.WorldToViewportPoint(groups[g].position).z).ToArray();
                feature.ResetAdaptiveToneHistory(camera);
                update = () => {
                    try {
                        if(EditorApplication.timeSinceStartup-started>100) {finish("timeout");return;}
                        if(lastFrame==Time.frameCount)return; lastFrame=Time.frameCount;
                        bool walk=cursor<FrameCount;
                        int group=cursor-FrameCount;
                        demo.Sample(walk ? cursor/(float)FrameCount : 0f);
                        if(walk) record.poses[cursor]=SamplePose(groups,bindAngles,record.bindPositions,camera,animator);
                        else {
                            for(int r=0;r<renderers.Length;r++)renderers[r].sharedMesh=partitions[group][r];
                            feature.ResetAdaptiveToneHistory(camera);
                        }
                        camera.Render(); AsyncGPUReadback.WaitAllRequests();
                        var active=RenderTexture.active;
                        try {
                            RenderTexture.active=target;
                            image.ReadPixels(new Rect(0,0,Width,Height),0,0); image.Apply();
                            File.WriteAllBytes(Evidence+"/"+(walk?"walk_":"part_")+(walk?cursor:group).ToString("D2")+".png",image.EncodeToPNG());
                        } finally {RenderTexture.active=active;}
                        cursor++;
                        if(cursor==FrameCount+groups.Length)finish("complete");
                    } catch(Exception ex) {finish("failed: "+ex);}
                };
                EditorApplication.update += update;
                EditorApplication.playModeStateChanged += onPlay;
                AssemblyReloadEvents.beforeAssemblyReload += onReload;
            } catch(Exception ex) {finish("failed: "+ex);throw;}
        }

        public static void PreparePartitions()
        {
            if(EditorApplication.isPlayingOrWillChangePlaymode || SceneManager.GetActiveScene().path!=ScenePath)
                throw new InvalidOperationException("Prepare partitions in the isolated Edit Mode scene.");
            string path=Root+"/Editor/BakePartitions.asset";
            if(File.Exists(path))throw new InvalidOperationException("Partitions already exist; no overwrite.");
            var demo=Object.FindFirstObjectByType<CharacterPipelineComparison>();
            var animator=demo.liveAnimator;
            var groups=Groups.Select(animator.GetBoneTransform).ToArray();
            if(groups.Any(b=>b==null))throw new InvalidOperationException("Missing humanoid mapping.");
            var renderers=animator.GetComponentInParent<CharacterSilhouetteSubject>().GetComponentsInChildren<SkinnedMeshRenderer>();
            EnsureFolder(Root+"/Editor");
            // Read weights in the editor, where imported read-disabled geometry is accessible.
            // No CPU-read copy is enabled on the gameplay model and no model reimport is needed.
            for(int g=0;g<groups.Length;g++)for(int r=0;r<renderers.Length;r++) {
                var mesh=CharacterPipelineMeshPartition.ExtractGroup(renderers[r],groups,g);
                mesh.name="group_"+g+"_renderer_"+r;
                if(g==0&&r==0)AssetDatabase.CreateAsset(mesh,path);
                else AssetDatabase.AddObjectToAsset(mesh,path);
            }
            AssetDatabase.SaveAssetIfDirty(AssetDatabase.LoadMainAssetAtPath(path));
            Debug.Log("Prepared 14 disjoint parts using editor mesh access; source model imports unchanged.");
        }

        private static Vector2Int Project(Vector3 point,Camera camera)
        {
            // 2D rig origin is the 3D model's ground origin; no screen-space camera offset baked into bones.
            return Vector2Int.RoundToInt(new Vector2(Vector3.Dot(point,camera.transform.right),Vector3.Dot(point,camera.transform.up))*Ppu);
        }

        private static float BoneAngle(Transform[] groups,int index,Camera camera,Animator animator)
        {
            Transform endpoint = index==0 ? animator.GetBoneTransform(HumanBodyBones.Chest) : null;
            for(int j=1;j<Parents.Length && endpoint==null;j++)if(Parents[j]==index)endpoint=groups[j];
            Vector3 axis = endpoint!=null ? endpoint.position-groups[index].position : groups[index].TransformDirection(Vector3.up);
            return Mathf.Atan2(Vector3.Dot(axis,camera.transform.up),Vector3.Dot(axis,camera.transform.right))*Mathf.Rad2Deg;
        }

        private static ModularSpriteMotionFrame SamplePose(Transform[] groups,float[] bindAngles,Vector2Int[] bind,Camera camera,Animator animator)
        {
            var poses = new ModularSpriteBonePose[groups.Length];
            var position=groups.Select(t=>Project(t.position,camera)).ToArray();
            var rotation=Enumerable.Range(0,groups.Length).Select(g=>Mathf.DeltaAngle(bindAngles[g],BoneAngle(groups,g,camera,animator))).ToArray();
            for(int g=0;g<groups.Length;g++) {
                int parent=Parents[g];
                float parentRotation=parent<0?0:rotation[parent];
                Vector2 difference=parent<0?position[g]:position[g]-position[parent];
                Vector2 local=Quaternion.Euler(0,0,-parentRotation)*difference;
                Vector2Int bindOffset=parent<0?bind[g]:bind[g]-bind[parent];
                poses[g]=new ModularSpriteBonePose(Vector2Int.RoundToInt(local)-bindOffset,rotation[g]-parentRotation);
            }
            return new ModularSpriteMotionFrame(poses);
        }

        public static void FinishAssets()
        {
            if(EditorApplication.isPlayingOrWillChangePlaymode || SceneManager.GetActiveScene().path!=ScenePath)
                throw new InvalidOperationException("Finish in Edit Mode in the prepared scene.");
            var record=JsonUtility.FromJson<BakeRecord>(File.ReadAllText(Evidence+"/bake.json"));
            if(record.status!="complete")throw new InvalidOperationException("Bake incomplete: "+record.status);
            if(AssetDatabase.LoadAssetAtPath<ModularSpriteRigDefinition>(Root+"/FrontRig.asset")!=null)
                throw new InvalidOperationException("Finished assets already exist; no automatic overwrite.");
            EnsureFolder(Root+"/Frames"); EnsureFolder(Root+"/Parts");
            var frames=new Sprite[FrameCount];
            for(int f=0;f<FrameCount;f++)frames[f]=ImportSprite(Evidence+"/walk_"+f.ToString("D2")+".png",Root+"/Frames/Walk_"+f.ToString("D2")+".png",new Vector2(.5f,.5f));
            var partSprites=new Sprite[Groups.Length];
            for(int g=0;g<Groups.Length;g++) {
                // Part positions and pivots must use the SAME integer-pixel attachment point.
                // Camera's world origin projects to (Width/2, Height/2 - 1.7*PPU).
                Vector2 pivotPixels=new Vector2(Width*.5f,Height*.5f-1.7f*Ppu)+record.bindPositions[g];
                var pivot=new Vector2(pivotPixels.x/Width,pivotPixels.y/Height);
                partSprites[g]=ImportSprite(Evidence+"/part_"+g.ToString("D2")+".png",Root+"/Parts/"+record.partIds[g]+".png",pivot);
            }
            var bones=Enumerable.Range(0,Groups.Length).Select(g=>new ModularSpriteBoneDefinition(record.partIds[g],Parents[g],Parents[g]<0?record.bindPositions[g]:record.bindPositions[g]-record.bindPositions[Parents[g]])).ToArray();
            var parts=Enumerable.Range(0,Groups.Length).Select(g=>new ModularSpritePartDefinition(record.partIds[g],g)).ToArray();
            var orders=Enumerable.Range(0,8).Select(f=>new ModularSpriteFacingLayerOrder((ModularSpriteFacing8)f,record.layerOrder.Select(g=>record.partIds[g]).ToArray())).ToArray();
            var rig=ScriptableObject.CreateInstance<ModularSpriteRigDefinition>();
            AssignData(rig,new ModularSpriteRigData(Ppu,bones,parts,orders));
            if(!rig.TryValidate(out string error))throw new InvalidOperationException(error);
            AssetDatabase.CreateAsset(rig,Root+"/FrontRig.asset");
            var skin=ScriptableObject.CreateInstance<ModularSpriteSkinDefinition>();
            AssignData(skin,new ModularSpriteSkinData("chibi_front_automatic_cutouts",Enumerable.Range(0,Groups.Length).Select(g=> {
                var directions=new Sprite[8]; directions[(int)ModularSpriteFacing8.South]=partSprites[g];
                return new ModularSpriteSkinPart(record.partIds[g],directions);
            }).ToArray()));
            AssetDatabase.CreateAsset(skin,Root+"/FrontSkin.asset");
            var motion=ScriptableObject.CreateInstance<ModularSpriteMotionDefinition>();
            AssignData(motion,new ModularSpriteMotionData("walk_projected_front",12,true,record.poses));
            AssetDatabase.CreateAsset(motion,Root+"/FrontWalk.asset");
            if(!skin.TryValidate(rig,false,out error)||!motion.TryValidate(rig,out error))throw new InvalidOperationException(error);
            var material=new Material(Shader.Find("Universal Render Pipeline/2D/Sprite-Unlit-Default"));
            if(material.shader==null)throw new InvalidOperationException("URP sprite unlit shader unavailable.");
            AssetDatabase.CreateAsset(material,Root+"/SpriteUnlit.mat");
            var demo=Object.FindFirstObjectByType<CharacterPipelineComparison>();
            var subject=demo.liveAnimator.GetComponentInParent<CharacterSilhouetteSubject>();
            subject.transform.position=new Vector3(Width/(float)Ppu,0,0);
            var baked=new GameObject("B_AutomaticallyBakedWalk").AddComponent<SpriteRenderer>();
            baked.transform.SetPositionAndRotation(new Vector3(0,1.7f,0),Quaternion.Euler(0,180,0));
            baked.sharedMaterial=material; baked.sprite=frames[0];
            var actor=new GameObject("C_FrontCutoutSkeleton").AddComponent<ModularSpriteActor>();
            actor.transform.SetPositionAndRotation(new Vector3(-Width/(float)Ppu,0,0),Quaternion.Euler(0,180,0));
            actor.AutoPlay=false;
            if(!actor.Configure(rig,skin,motion,material))throw new InvalidOperationException(actor.LastError);
            demo.bakedActor=baked; demo.bakedFrames=frames; demo.cutoutActor=actor; demo.animate=true;
            Camera.main.backgroundColor=new Color(.13f,.15f,.18f,1);
            Camera.main.aspect=3f*Width/Height;
            foreach(var asset in new Object[]{rig,skin,motion,material}) AssetDatabase.SaveAssetIfDirty(asset);
            EditorSceneManager.SaveScene(SceneManager.GetActiveScene(),ScenePath);
            CleanBakeInputs();
            Debug.Log("Built A/B/C comparison. 16 automatic sprites, 14 fixed cutouts, existing modular rig/skin/motion API. Front only; no Smack depth reconstruction.");
        }

        public static void CleanBakeInputs()
        {
            string path=Root+"/Editor/BakePartitions.asset";
            if(!File.Exists(path))return;
            if(AssetDatabase.GetDependencies(ScenePath,true).Contains(path))
                throw new InvalidOperationException("Comparison still references bake-only meshes; retaining them.");
            // These are this builder's reproducible temporary meshes, never source models.
            if(!AssetDatabase.DeleteAsset(path))throw new IOException("Could not remove bake-only mesh asset.");
        }

        private static void AssignData<T>(Object asset,T data)
        {
            // Existing definition data stays serialized through its original owner, not parallel runtime DTOs.
            JsonUtility.FromJsonOverwrite("{\"data\":"+JsonUtility.ToJson(data)+"}",asset);
            EditorUtility.SetDirty(asset);
        }

        private static Sprite ImportSprite(string source,string target,Vector2 pivot)
        {
            if(!File.Exists(target)) File.Copy(source,target,false);
            else if(!File.ReadAllBytes(source).SequenceEqual(File.ReadAllBytes(target)))
                throw new InvalidOperationException("Different existing image is preserved: "+target);
            AssetDatabase.ImportAsset(target,ImportAssetOptions.ForceSynchronousImport);
            var importer=(TextureImporter)AssetImporter.GetAtPath(target);
            importer.textureType=TextureImporterType.Sprite;
            importer.spriteImportMode=SpriteImportMode.Single;
            importer.spritePixelsPerUnit=Ppu;
            importer.filterMode=FilterMode.Point;
            importer.mipmapEnabled=false;
            importer.textureCompression=TextureImporterCompression.Uncompressed;
            importer.alphaSource=TextureImporterAlphaSource.FromInput;
            importer.alphaIsTransparency=true;
            importer.maxTextureSize=512;
            var settings=new TextureImporterSettings(); importer.ReadTextureSettings(settings);
            settings.spriteAlignment=(int)SpriteAlignment.Custom; settings.spritePivot=pivot;
            settings.spriteMeshType=SpriteMeshType.FullRect;
            importer.SetTextureSettings(settings); importer.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Sprite>(target);
        }

        private static Light MakeLight(string name,float intensity,Vector3 rotation)
        {
            var light=new GameObject(name).AddComponent<Light>();
            light.type=LightType.Directional; light.intensity=intensity; light.color=Color.white;
            light.transform.rotation=Quaternion.Euler(rotation); light.shadows=LightShadows.None;
            return light;
        }

        private static void EnsureFolder(string path)
        {
            if(AssetDatabase.IsValidFolder(path))return;
            string parent=Path.GetDirectoryName(path).Replace('\\','/');
            EnsureFolder(parent); AssetDatabase.CreateFolder(parent,Path.GetFileName(path));
        }
    }
}
