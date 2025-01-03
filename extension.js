const cursor = require('cursor');

let isEnabled = true;

function activate(context) {
    console.log('Cursor Auto Accept is now active');

    // Register the toggle command
    let toggleCommand = cursor.commands.registerCommand('cursor-auto-accept.toggle', () => {
        isEnabled = !isEnabled;
        cursor.window.showInformationMessage(
            `Auto Accept is now ${isEnabled ? 'enabled' : 'disabled'}`
        );
    });

    // Add command to context
    context.subscriptions.push(toggleCommand);

    // Listen for AI prompt events
    cursor.workspace.onDidShowAIPrompt((prompt) => {
        if (isEnabled) {
            prompt.accept();
        }
    });
}

function deactivate() {
    console.log('Cursor Auto Accept is now deactivated');
}

module.exports = {
    activate,
    deactivate
}; 