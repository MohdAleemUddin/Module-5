import * as vscode from 'vscode';
import { registerPiiRedaction } from './modules/m5_observability/quickfix/piiRedaction';

export function activate(context: vscode.ExtensionContext) {
  const disposable = vscode.commands.registerCommand('zeroui.m5.openPanel', () => {
    vscode.window.showInformationMessage('Module 5 Panel opened');
  });

  const treeDataProvider = new M5TreeDataProvider();
  vscode.window.registerTreeDataProvider('zeroUI.view.main', treeDataProvider);

  registerPiiRedaction(context);
  context.subscriptions.push(disposable);
}

export function deactivate() {}

class M5TreeDataProvider implements vscode.TreeDataProvider<M5TreeItem> {
  getTreeItem(element: M5TreeItem): vscode.TreeItem {
    return element;
  }

  getChildren(element?: M5TreeItem): Thenable<M5TreeItem[]> {
    if (!element) {
      return Promise.resolve([
        new M5TreeItem('Module 5 not wired yet', vscode.TreeItemCollapsibleState.None)
      ]);
    }
    return Promise.resolve([]);
  }
}

class M5TreeItem extends vscode.TreeItem {
  constructor(
    public readonly label: string,
    public readonly collapsibleState: vscode.TreeItemCollapsibleState
  ) {
    super(label, collapsibleState);
  }
}

