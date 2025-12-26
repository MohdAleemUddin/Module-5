import * as vscode from 'vscode';

export function activate(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('zeroui.m5.openPanel', () => {
    vscode.window.showInformationMessage('Module 5 Panel Opened');
  });

  const treeDataProvider = new M5TreeDataProvider();
  const treeView = vscode.window.registerTreeDataProvider('zeroUI.view.main', treeDataProvider);

  context.subscriptions.push(disposable, treeView);
}

export function deactivate() {}

class M5TreeDataProvider implements vscode.TreeDataProvider<vscode.TreeItem> {
  getTreeItem(element: vscode.TreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: vscode.TreeItem): Thenable<vscode.TreeItem[]> {
    if (!element) {
      const item = new vscode.TreeItem('Module 5 not wired yet');
      return Promise.resolve([item]);
    }
    return Promise.resolve([]);
  }
}

