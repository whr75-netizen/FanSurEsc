using FantasySurvival.Inventory;
using FantasySurvival.SaveSystem;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.UI;

public class MainMenuManager : MonoBehaviour
{
    [Header("Panels")]
    [SerializeField] private GameObject mainPanel;
    [SerializeField] private GameObject loadPanel;
    [SerializeField] private GameObject settingsPanel;
    [SerializeField] private GameObject exitPanel;

    [Header("Load Slot")]
    [SerializeField] private ItemDatabase itemDatabase;
    [SerializeField] private Text loadSlotText;
    [SerializeField] private Button loadSlotButton;

    [Header("Settings")]
    [SerializeField] private Toggle soundToggle;

    [Header("Status")]
    [SerializeField] private Text statusText;

    private GameSaveData cachedSave;

    private void Awake()
    {
        GameUserSettings.Apply();
        ShowMainPanel();
    }

    public void StartGame()
    {
        StartNewGame();
    }

    public void StartNewGame()
    {
        GameStartRequest.QueueNewGame();
        SceneManager.LoadScene("GameLoadingScene");
    }

    public void OpenLoadPanel()
    {
        bool canLoad = TrySelectLoadCandidate(out bool loadedBackup, out string status);

        if (canLoad)
        {
            loadSlotText.text = loadedBackup
                ? $"Slot 1  {GameSaveManager.GetDisplayTimestamp(cachedSave)}  (backup recovered)"
                : $"Slot 1  {GameSaveManager.GetDisplayTimestamp(cachedSave)}";
            SetStatus(status);
        }
        else
        {
            loadSlotText.text = "Slot 1  Empty or unavailable";
            SetStatus(status);
        }

        if (loadSlotButton != null)
        {
            loadSlotButton.interactable = canLoad;
        }

        ShowOnly(loadPanel);
    }

    public void LoadSelectedGame()
    {
        if (cachedSave == null && !TrySelectLoadCandidate(out _, out string error))
        {
            SetStatus(error);
            return;
        }

        if (!GameStartRequest.QueueLoad(cachedSave))
        {
            SetStatus("Could not queue the selected save.");
            return;
        }

        SceneManager.LoadScene("GameLoadingScene");
    }

    private bool TrySelectLoadCandidate(out bool loadedBackup, out string status)
    {
        cachedSave = null;
        loadedBackup = false;

        GameSaveManager.ReadSlotOneCandidates(
            out GameSaveData primary,
            out string primaryReadError,
            out GameSaveData backup,
            out string backupReadError);

        if (TryValidateLoadCandidate(primary, out string primaryValidationError))
        {
            cachedSave = primary;
            status = string.Empty;
            return true;
        }

        if (TryValidateLoadCandidate(backup, out string backupValidationError))
        {
            cachedSave = backup;
            loadedBackup = true;
            status = "Primary save was invalid; a validated backup will be loaded.";
            return true;
        }

        status = $"Primary: {CombineReadAndValidationError(primaryReadError, primaryValidationError)} " +
                 $"Backup: {CombineReadAndValidationError(backupReadError, backupValidationError)}";
        return false;
    }

    private bool TryValidateLoadCandidate(GameSaveData candidate, out string error)
    {
        if (candidate == null)
        {
            error = "No readable save.";
            return false;
        }

        return InventorySaveCodec.TryRestore(
            candidate.playerInventory,
            itemDatabase,
            InventoryUIManager.DefaultInventoryWidth,
            InventoryUIManager.DefaultInventoryHeight,
            out _,
            out error);
    }

    private static string CombineReadAndValidationError(string readError, string validationError)
    {
        return string.IsNullOrWhiteSpace(readError) ? validationError : readError;
    }

    public void OpenSettingsPanel()
    {
        if (soundToggle != null)
        {
            soundToggle.SetIsOnWithoutNotify(GameUserSettings.SoundEnabled);
        }

        ShowOnly(settingsPanel);
        SetStatus(string.Empty);
    }

    public void SetSoundEnabled(bool enabled)
    {
        GameUserSettings.SetSoundEnabled(enabled);
        SetStatus(enabled ? "Sound enabled." : "Sound disabled.");
    }

    public void OpenExitPanel()
    {
        ShowOnly(exitPanel);
        SetStatus(string.Empty);
    }

    public void ShowMainPanel()
    {
        cachedSave = null;
        ShowOnly(mainPanel);
        SetStatus(string.Empty);
    }

    public void QuitGame()
    {
#if UNITY_EDITOR
        Debug.Log("Quit requested. Application.Quit only closes a built player.", this);
#endif
        Application.Quit();
    }

    private void ShowOnly(GameObject panel)
    {
        if (mainPanel != null) mainPanel.SetActive(panel == mainPanel);
        if (loadPanel != null) loadPanel.SetActive(panel == loadPanel);
        if (settingsPanel != null) settingsPanel.SetActive(panel == settingsPanel);
        if (exitPanel != null) exitPanel.SetActive(panel == exitPanel);
    }

    private void SetStatus(string message)
    {
        if (statusText != null)
        {
            statusText.text = message ?? string.Empty;
        }
    }
}
