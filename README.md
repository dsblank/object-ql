# object-ql

An Object Query Language, for the [Gramps Project](https://gramps-project.org/) and other objects.

This project is designed to be a drop-in replacement for https://github.com/DavidMStraub/gramps-ql

Rather than having to build, and learn, a new query language, the idea
is to build on top of Python, the native language of the Gramps Project.
And, rather than having to convert the Gramps raw data into objects, then dicts, and
then back again to objects (when needed), this query system can operate directly
on the objects.

Each object can be identified by its lower-case class type, eg `person`, `note`, `family`, etc.

Examples:

Find the person with a particular gramps_id:

```python
person.gramps_id == 'person001'
```

Find all of the people with notes:

```python
person.get_note_list()
```
Find all of the people with notes that mention 'vote':

```python
any([('vote' in str(get_note(handle).text)) for handle in person.get_note_list()])
```

## Usage

If you don't know what the type is, you can use `obj`, like:

```python
"23" in obj.gramps_id
```
You can use standard dot notation to reference any object. Refer to [Gramps Primary Objects](https://www.gramps-project.org/wiki/index.php/Using_database_API#Primary_Objects) for the structure of Gramps objects.

You can also use the `SimpleAccess` methods that make access to some data much easier. The [SimpleAccess](https://gramps-project.org/docs/simple.html#module-gramps.gen.simple._simpleaccess) is available as `sa`, as shown below.

Select all of the people that have are married to a person named "Donna":

```python
sa.first_name(sa.spouse(person)) == "Donna"
```
