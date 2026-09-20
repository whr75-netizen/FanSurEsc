using System;
using System.IO;
using System.Linq;
using FantasySurvival.CharacterPresentation;
using FantasySurvival.SceneFlow;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

// A placement review of the existing asset, not a new rendering pipeline.
public static class PixelDeskEightDirectionReview
{
    public const string RootName = "PixelDeskEightDirections_D24";
    const string Output = "LocalOnly/WorkLoop/desk-eight-directions24";

    [Serializable] class CameraRecord
    {
        public Vector3 position, rotation, player;
        public float orthographicSize;
        public int width, height;
        public Vector3[] groundCorners;
    }
    [Serializable] class DeskRecord
    {
        public string name;
        public float yaw;
        public Vector3 position, boundsSize;
        public int meshCount, pixelCellSize;
    }
    [Serializable] class LayoutRecord
    {
        public string scene, originalComparison;
        public bool originalPreservedInactive;
        public DeskRecord[] desks;
    }
    [Serializable] class PlayRecord
    {
        public string camera, scene, captureMethod;
        public Vector3 position, rotation, playerPosition;
        public float orthographicSize;
        public int width, height, deskCount;
        public bool targetTextureIsNull, cameraSettingsUntouched;
    }

    [MenuItem("Tools/Pixel Desk/Place Eight Directions in Original Play View")]
    public static void Place()
    {
        if (EditorApplication.isPlaying || SceneManager.GetActiveScene().name != "GameMap1")
            throw new InvalidOperationException("Edit-mode GameMap1 required.");
        if (GameObject.Find(RootName) != null)
            throw new InvalidOperationException("Review already exists; do not regenerate it.");
        var original = GameObject.Find(PixelDeskLightingProbe.RootName);
        if (original == null) throw new InvalidOperationException("Existing comparison required.");
        var source = original.transform.Find("B_Actual12Meshes_LiveShading").gameObject;
        var camera = JsonUtility.FromJson<CameraRecord>(File.ReadAllText(
            "LocalOnly/PixelUnityProbe24/original-play-camera.json"));
        var root = new GameObject(RootName);
        Undo.RegisterCreatedObjectUndo(root, "Place eight existing desk directions");
        var record = new LayoutRecord
        {
            scene = SceneManager.GetActiveScene().path,
            originalComparison = original.name,
            originalPreservedInactive = true,
            desks = new DeskRecord[8]
        };
        for (int i = 0; i < 8; i++)
        {
            // Ground intersections measured from the unchanged, normal Play camera.
            float x = .17f + (i % 4) * .22f;
            float y = i < 4 ? .36f : .16f;
            Vector3 position = camera.groundCorners[0]
                + (camera.groundCorners[1] - camera.groundCorners[0]) * ((x - .1f) / .8f)
                + (camera.groundCorners[2] - camera.groundCorners[0]) * ((y - .1f) / .8f);
            position.y = 0f;
            var desk = UnityEngine.Object.Instantiate(source, root.transform);
            desk.name = "Desk_" + (i * 45).ToString("000") + "deg";
            desk.transform.SetPositionAndRotation(position, Quaternion.Euler(0f, i * 45f, 0f));
            desk.SetActive(true);
            var renderers = desk.GetComponentsInChildren<MeshRenderer>();
            Bounds bounds = renderers[0].bounds;
            foreach (var renderer in renderers) bounds.Encapsulate(renderer.bounds);
            record.desks[i] = new DeskRecord
            {
                name = desk.name, yaw = i * 45f, position = position, boundsSize = bounds.size,
                meshCount = renderers.Length,
                pixelCellSize = desk.GetComponent<CharacterSilhouetteSubject>().PixelCellSize
            };
            var labelObject = new GameObject("Angle_" + (i * 45));
            labelObject.transform.SetParent(root.transform, false);
            Vector3 towardCamera = Quaternion.Euler(0f, camera.rotation.y, 0f) * Vector3.back;
            labelObject.transform.SetPositionAndRotation(
                position + towardCamera * 1.05f + Vector3.up * .08f,
                Quaternion.Euler(camera.rotation));
            var label = labelObject.AddComponent<TextMesh>();
            label.text = (i * 45) + "°";
            label.anchor = TextAnchor.MiddleCenter;
            label.alignment = TextAlignment.Center;
            label.fontSize = 48;
            label.characterSize = .055f;
            label.color = Color.white;
        }
        Undo.RecordObject(original, "Hide preserved two-desk comparison during eight-direction review");
        original.SetActive(false);
        PrefabUtility.RecordPrefabInstancePropertyModifications(original);
        Directory.CreateDirectory(Output);
        File.WriteAllText(Output + "/layout.json", JsonUtility.ToJson(record, true));
        EditorSceneManager.MarkSceneDirty(SceneManager.GetActiveScene());
        EditorSceneManager.SaveScene(SceneManager.GetActiveScene());
        Selection.activeGameObject = root;
    }

    static string capturePath;
    static int startFrame;
    static bool screenshotRequested, oldRunInBackground;

    [MenuItem("Tools/Pixel Desk/Inspect Eight Directions with Normal Player Camera")]
    public static void InspectWithNormalPlayerCamera()
    {
        if (!EditorApplication.isPlaying || PersistentGameplayShell.Instance == null)
            throw new InvalidOperationException("Press Play in GameMap1 first.");
        var root = GameObject.Find(RootName);
        if (root == null) throw new InvalidOperationException("Eight-direction review missing.");
        var shell = PersistentGameplayShell.Instance;
        string error;
        if (!shell.PlayerMovement.TryTeleport(root.transform.position + Vector3.up * .5f,
                shell.PlayerTransform.rotation, out error))
            throw new InvalidOperationException(error);
        // The existing CameraFollow alone updates the camera on its normal tick.
    }

    [MenuItem("Tools/Pixel Desk/Capture Unchanged Play Game View")]
    public static void CaptureUnchangedGameView()
        => CaptureUnchangedGameView(Output);

    public static void CaptureUnchangedGameView(string outputDirectory)
    {
        if (!EditorApplication.isPlaying || PersistentGameplayShell.Instance == null)
            throw new InvalidOperationException("Normal base Play required.");
        if (capturePath != null) throw new InvalidOperationException("Capture already pending.");
        string path = Path.GetFullPath(outputDirectory + "/preview.png");
        if (File.Exists(path)) throw new InvalidOperationException("Previous capture must be preserved.");
        var camera = PersistentGameplayShell.Instance.PlayerCamera;
        if (camera.targetTexture != null) throw new InvalidOperationException("Expected real display camera.");
        var root = GameObject.Find(RootName);
        var record = new PlayRecord
        {
            camera = camera.name, scene = SceneManager.GetActiveScene().name,
            captureMethod = "ScreenCapture.CaptureScreenshot; original Game View including UI",
            position = camera.transform.position, rotation = camera.transform.eulerAngles,
            playerPosition = PersistentGameplayShell.Instance.PlayerTransform.position,
            orthographicSize = camera.orthographicSize, width = camera.pixelWidth, height = camera.pixelHeight,
            deskCount = root.GetComponentsInChildren<CharacterSilhouetteSubject>().Length,
            targetTextureIsNull = true, cameraSettingsUntouched = true
        };
        Directory.CreateDirectory(outputDirectory);
        File.WriteAllText(outputDirectory + "/camera.json", JsonUtility.ToJson(record, true));
        capturePath = path;
        startFrame = Time.frameCount;
        screenshotRequested = false;
        oldRunInBackground = Application.runInBackground;
        Application.runInBackground = true;
        EditorApplication.update += CaptureUpdate;
    }

    static void CaptureUpdate()
    {
        if (!EditorApplication.isPlaying) { FinishCapture(); return; }
        if (!screenshotRequested && Time.frameCount >= startFrame + 3)
        {
            ScreenCapture.CaptureScreenshot(capturePath, 1);
            screenshotRequested = true;
        }
        if (screenshotRequested && File.Exists(capturePath))
        {
            Debug.Log("Eight directions: unchanged Play Game View saved to " + capturePath);
            FinishCapture();
            return;
        }
        EditorApplication.QueuePlayerLoopUpdate();
    }

    static void FinishCapture()
    {
        EditorApplication.update -= CaptureUpdate;
        Application.runInBackground = oldRunInBackground;
        capturePath = null;
    }
}
