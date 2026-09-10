using FantasySurvival.CharacterPresentation.ModularSprites;
using UnityEngine;

namespace FantasySurvival.CharacterPresentation
{
    /// <summary>Isolated authoring comparison, never attached to the gameplay shell.</summary>
    public sealed class CharacterPipelineComparison : MonoBehaviour
    {
        public Animator liveAnimator;
        public SpriteRenderer bakedActor;
        public Sprite[] bakedFrames;
        public ModularSpriteActor cutoutActor;
        public Light keyLight;
        [Min(.01f)] public float cycleSeconds = 4f / 3f;
        public bool animate = true;
        [Range(0f, 1f)] public float phase;
        [Range(.05f, 3f)] public float lightIntensity = 2f;
        private static readonly int Locomotion = Animator.StringToHash("Base Layer.Locomotion");
        private static readonly int Speed = Animator.StringToHash("LocomotionSpeed");

        private void Start()
        {
            if (cutoutActor != null) cutoutActor.AutoPlay = false;
            Sample(phase);
        }

        private void Update()
        {
            if (animate) phase = Mathf.Repeat(phase + Time.deltaTime / Mathf.Max(.01f, cycleSeconds), 1f);
            Sample(phase);
        }

        public void Sample(float normalizedPhase)
        {
            phase = Mathf.Repeat(normalizedPhase, 1f);
            if (liveAnimator != null)
            {
                // This test owns only its presentation Animator. No Player input or controller.
                liveAnimator.enabled = true;
                liveAnimator.applyRootMotion = false;
                liveAnimator.SetFloat(Speed, 1f);
                liveAnimator.Play(Locomotion, 0, phase);
                liveAnimator.Update(0f);
                liveAnimator.enabled = false;
            }
            if (bakedActor != null && bakedFrames != null && bakedFrames.Length > 0)
                bakedActor.sprite = bakedFrames[Mathf.FloorToInt(phase * bakedFrames.Length) % bakedFrames.Length];
            if (cutoutActor != null) cutoutActor.SampleAt(phase * cycleSeconds);
            if (keyLight != null) keyLight.intensity = lightIntensity;
        }

        private void OnGUI()
        {
            float width = Screen.width / 3f;
            var label = new GUIStyle(GUI.skin.label) { alignment = TextAnchor.UpperCenter, fontSize = 16 };
            GUI.Label(new Rect(0, 12, width, 60), "A · LIVE 3D\nDynamic lighting / skeleton", label);
            GUI.Label(new Rect(width, 12, width, 60), "B · BAKED SPRITES\n16 frames / captured lighting", label);
            GUI.Label(new Rect(width * 2, 12, width, 60), "C · 2D BONES\n14 fixed parts / front only", label);
            GUILayout.BeginArea(new Rect(14, Screen.height - 100, Screen.width - 28, 94), GUI.skin.box);
            GUILayout.BeginHorizontal();
            if (GUILayout.Button(animate ? "Pause" : "Play", GUILayout.Width(80))) animate = !animate;
            GUILayout.Label("Pose", GUILayout.Width(40));
            phase = GUILayout.HorizontalSlider(phase, 0, .9999f, GUILayout.Width(220));
            GUILayout.Label("Live light", GUILayout.Width(75));
            lightIntensity = GUILayout.HorizontalSlider(lightIntensity, .05f, 3f, GUILayout.Width(220));
            GUILayout.EndHorizontal();
            GUILayout.Label("Same source + walk. B/C deliberately keep baked light; C is planar cutout animation, NOT depth reconstruction.");
            GUILayout.EndArea();
        }
    }
}
