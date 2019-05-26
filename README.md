# Tree Mounter

Easiest way of managing/creating file-tree structure.


```python
from mounter import Dir, File


root = Dir('root')(
    Dir('MyFolder')(
        File('file1.txt'),
        File('file2.txt'),
        Dir('MyFolder2')(
            File('file3.txt')
        )
    ),
    Dir('My2Folder')(
        # in-memory file with basic content
        File('file1.txt', 'content'),
        File('file1.txt'),
        Dir('MyFolder2')(
            File('file3.txt')
        )
    )
)

# Mount that tree to current directory
root.mount('./')
```

For your tests use `tmpmount`:

```python
from mounter import Dir, File, tmpmount


root = Dir('root')(
    Dir('another')(
        Dir('hidden')(
            File('file3.txt')
        )
    )
)

with tmpmount(root, mount='./'):
    pass
    
# cleaned up
    
```

You can do all basic operations(`cd`, `rm`) on that tree.
like, iterating through all elements including children, searching, and printing the tree:
```
>>> root.tree()
```

```bash
MyFolder
   file1.txt
   file2.txt
   MyFolder2
      file3.txt
My2Folder
   file1.txt
   file1.txt
   MyFolder2
      file3.txt

```





