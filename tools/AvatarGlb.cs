using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Text;

public static class AvatarGlb
{
    public static int Main(string[] args)
    {
        string path = args != null && args.Length > 0 ? args[0] : "models\\avatar.glb";
        Build(path);
        Console.WriteLine("Wrote " + path);
        return 0;
    }
    struct Vec3
    {
        public float X, Y, Z;
        public Vec3(float x, float y, float z) { X = x; Y = y; Z = z; }
        public static Vec3 operator +(Vec3 a, Vec3 b) { return new Vec3(a.X + b.X, a.Y + b.Y, a.Z + b.Z); }
        public static Vec3 operator -(Vec3 a, Vec3 b) { return new Vec3(a.X - b.X, a.Y - b.Y, a.Z - b.Z); }
        public static Vec3 operator *(Vec3 a, float s) { return new Vec3(a.X * s, a.Y * s, a.Z * s); }
        public float Length() { return (float)Math.Sqrt(X * X + Y * Y + Z * Z); }
        public Vec3 Normalized()
        {
            float l = Length();
            if (l < 1e-8f) return new Vec3(0, 1, 0);
            return new Vec3(X / l, Y / l, Z / l);
        }
        public static Vec3 Cross(Vec3 a, Vec3 b)
        {
            return new Vec3(a.Y * b.Z - a.Z * b.Y, a.Z * b.X - a.X * b.Z, a.X * b.Y - a.Y * b.X);
        }
    }

    class MeshData
    {
        public List<float> Pos = new List<float>();
        public List<float> Nor = new List<float>();
        public List<int> Idx = new List<int>();
        public int VertCount { get { return Pos.Count / 3; } }

        public void AddTri(Vec3 a, Vec3 b, Vec3 c)
        {
            Vec3 n = Vec3.Cross(b - a, c - a).Normalized();
            int i = VertCount;
            Push(a, n); Push(b, n); Push(c, n);
            Idx.Add(i); Idx.Add(i + 1); Idx.Add(i + 2);
        }

        void Push(Vec3 p, Vec3 n)
        {
            Pos.Add(p.X); Pos.Add(p.Y); Pos.Add(p.Z);
            Nor.Add(n.X); Nor.Add(n.Y); Nor.Add(n.Z);
        }

        public void Ellipsoid(Vec3 c, Vec3 r, int slices, int stacks)
        {
            int start = VertCount;
            for (int y = 0; y <= stacks; y++)
            {
                float v = (float)y / stacks;
                float phi = (float)(v * Math.PI);
                float sy = (float)Math.Sin(phi);
                float cy = (float)Math.Cos(phi);
                for (int x = 0; x <= slices; x++)
                {
                    float u = (float)x / slices;
                    float th = (float)(u * Math.PI * 2);
                    float ct = (float)Math.Cos(th);
                    float st = (float)Math.Sin(th);
                    Vec3 n = new Vec3(sy * ct, cy, sy * st);
                    Vec3 p = new Vec3(c.X + r.X * n.X, c.Y + r.Y * n.Y, c.Z + r.Z * n.Z);
                    Pos.Add(p.X); Pos.Add(p.Y); Pos.Add(p.Z);
                    Nor.Add(n.X); Nor.Add(n.Y); Nor.Add(n.Z);
                }
            }
            int stride = slices + 1;
            for (int y = 0; y < stacks; y++)
            {
                for (int x = 0; x < slices; x++)
                {
                    int a = start + y * stride + x;
                    int b = a + stride;
                    Idx.Add(a); Idx.Add(a + 1); Idx.Add(b);
                    Idx.Add(a + 1); Idx.Add(b + 1); Idx.Add(b);
                }
            }
        }

        public void CapsuleY(Vec3 c, float radius, float body, int slices)
        {
            Ellipsoid(new Vec3(c.X, c.Y + body * 0.5f, c.Z), new Vec3(radius, radius, radius), slices, 8);
            Ellipsoid(new Vec3(c.X, c.Y - body * 0.5f, c.Z), new Vec3(radius, radius, radius), slices, 8);
            int stacks = 8;
            int start = VertCount;
            for (int y = 0; y <= stacks; y++)
            {
                float t = (float)y / stacks;
                float yy = c.Y - body * 0.5f + body * t;
                for (int x = 0; x <= slices; x++)
                {
                    float u = (float)x / slices;
                    float th = (float)(u * Math.PI * 2);
                    Vec3 n = new Vec3((float)Math.Cos(th), 0, (float)Math.Sin(th));
                    Pos.Add(c.X + n.X * radius); Pos.Add(yy); Pos.Add(c.Z + n.Z * radius);
                    Nor.Add(n.X); Nor.Add(0); Nor.Add(n.Z);
                }
            }
            int stride = slices + 1;
            for (int y = 0; y < stacks; y++)
            {
                for (int x = 0; x < slices; x++)
                {
                    int a = start + y * stride + x;
                    int b = a + stride;
                    Idx.Add(a); Idx.Add(a + 1); Idx.Add(b);
                    Idx.Add(a + 1); Idx.Add(b + 1); Idx.Add(b);
                }
            }
        }

        public void CapsuleBetween(Vec3 a, Vec3 b, float radius, int slices)
        {
            Vec3 d = b - a;
            float len = d.Length();
            Vec3 axis = d.Normalized();
            Vec3 tmp = Math.Abs(axis.Y) < 0.9f ? new Vec3(0, 1, 0) : new Vec3(1, 0, 0);
            Vec3 u = Vec3.Cross(axis, tmp).Normalized();
            Vec3 v = Vec3.Cross(axis, u).Normalized();
            Ellipsoid(a, new Vec3(radius, radius, radius), slices, 8);
            Ellipsoid(b, new Vec3(radius, radius, radius), slices, 8);
            int stacks = 8;
            int start = VertCount;
            for (int y = 0; y <= stacks; y++)
            {
                float t = (float)y / stacks;
                Vec3 c = a + d * t;
                for (int x = 0; x <= slices; x++)
                {
                    float th = (float)(x / (float)slices * Math.PI * 2);
                    Vec3 n = u * (float)Math.Cos(th) + v * (float)Math.Sin(th);
                    Vec3 p = c + n * radius;
                    Pos.Add(p.X); Pos.Add(p.Y); Pos.Add(p.Z);
                    Nor.Add(n.X); Nor.Add(n.Y); Nor.Add(n.Z);
                }
            }
            int stride = slices + 1;
            for (int y = 0; y < stacks; y++)
            {
                for (int x = 0; x < slices; x++)
                {
                    int i0 = start + y * stride + x;
                    int i1 = i0 + stride;
                    Idx.Add(i0); Idx.Add(i0 + 1); Idx.Add(i1);
                    Idx.Add(i0 + 1); Idx.Add(i1 + 1); Idx.Add(i1);
                }
            }
        }
    }

    class Mat
    {
        public string Name;
        public float[] Color;
        public float Metallic;
        public float Roughness;
        public Mat(string name, float r, float g, float b, float metallic, float roughness)
        {
            Name = name;
            Color = new float[] { r, g, b, 1 };
            Metallic = metallic;
            Roughness = roughness;
        }
    }

    static string F(float v)
    {
        return v.ToString("G9", CultureInfo.InvariantCulture);
    }

    static void MinMax(List<float> src, int stride, out float[] min, out float[] max)
    {
        min = new float[stride];
        max = new float[stride];
        for (int s = 0; s < stride; s++) { min[s] = float.PositiveInfinity; max[s] = float.NegativeInfinity; }
        for (int i = 0; i < src.Count; i += stride)
        {
            for (int s = 0; s < stride; s++)
            {
                float val = src[i + s];
                if (val < min[s]) min[s] = val;
                if (val > max[s]) max[s] = val;
            }
        }
    }

    static int Align4(int n) { return (n + 3) & ~3; }

    static string Arr(float[] a)
    {
        StringBuilder sb = new StringBuilder();
        sb.Append("[");
        for (int i = 0; i < a.Length; i++)
        {
            if (i > 0) sb.Append(",");
            sb.Append(F(a[i]));
        }
        sb.Append("]");
        return sb.ToString();
    }

    public static void Build(string path)
    {
        var skin = new MeshData();
        var hair = new MeshData();
        var sweater = new MeshData();
        var pants = new MeshData();
        var shoes = new MeshData();
        var eyeWhite = new MeshData();
        var iris = new MeshData();
        var dark = new MeshData();

        int S = 18;

        // Shoes
        shoes.Ellipsoid(new Vec3(-0.10f, 0.045f, 0.04f), new Vec3(0.075f, 0.045f, 0.13f), S, 10);
        shoes.Ellipsoid(new Vec3(0.10f, 0.045f, 0.04f), new Vec3(0.075f, 0.045f, 0.13f), S, 10);

        // Legs (pants)
        pants.CapsuleY(new Vec3(-0.10f, 0.28f, 0), 0.055f, 0.28f, S);
        pants.CapsuleY(new Vec3(0.10f, 0.28f, 0), 0.055f, 0.28f, S);
        pants.CapsuleY(new Vec3(-0.105f, 0.60f, 0), 0.075f, 0.30f, S);
        pants.CapsuleY(new Vec3(0.105f, 0.60f, 0), 0.075f, 0.30f, S);
        pants.Ellipsoid(new Vec3(0, 0.88f, 0.01f), new Vec3(0.17f, 0.12f, 0.11f), S, 12);

        // Sweater torso
        sweater.Ellipsoid(new Vec3(0, 1.08f, 0.02f), new Vec3(0.17f, 0.12f, 0.12f), S, 12);
        sweater.Ellipsoid(new Vec3(0, 1.26f, 0.01f), new Vec3(0.18f, 0.20f, 0.13f), S, 14);
        sweater.Ellipsoid(new Vec3(-0.20f, 1.36f, 0), new Vec3(0.08f, 0.07f, 0.08f), 14, 10);
        sweater.Ellipsoid(new Vec3(0.20f, 1.36f, 0), new Vec3(0.08f, 0.07f, 0.08f), 14, 10);
        sweater.CapsuleBetween(new Vec3(-0.22f, 1.34f, 0), new Vec3(-0.30f, 1.08f, 0.04f), 0.055f, 14);
        sweater.CapsuleBetween(new Vec3(0.22f, 1.34f, 0), new Vec3(0.30f, 1.08f, 0.04f), 0.055f, 14);

        // Forearms + hands (skin)
        skin.CapsuleBetween(new Vec3(-0.30f, 1.08f, 0.04f), new Vec3(-0.28f, 0.86f, 0.08f), 0.042f, 12);
        skin.CapsuleBetween(new Vec3(0.30f, 1.08f, 0.04f), new Vec3(0.28f, 0.86f, 0.08f), 0.042f, 12);
        skin.Ellipsoid(new Vec3(-0.27f, 0.80f, 0.10f), new Vec3(0.045f, 0.07f, 0.03f), 12, 8);
        skin.Ellipsoid(new Vec3(0.27f, 0.80f, 0.10f), new Vec3(0.045f, 0.07f, 0.03f), 12, 8);

        // Neck + head
        skin.CapsuleY(new Vec3(0, 1.46f, 0.01f), 0.045f, 0.07f, 12);
        skin.Ellipsoid(new Vec3(0, 1.60f, 0.02f), new Vec3(0.105f, 0.13f, 0.11f), 20, 16);
        skin.Ellipsoid(new Vec3(-0.105f, 1.58f, 0.01f), new Vec3(0.018f, 0.03f, 0.02f), 10, 8);
        skin.Ellipsoid(new Vec3(0.105f, 1.58f, 0.01f), new Vec3(0.018f, 0.03f, 0.02f), 10, 8);
        skin.Ellipsoid(new Vec3(0, 1.55f, 0.12f), new Vec3(0.025f, 0.02f, 0.02f), 10, 8);

        // Hair: short rounded volume + bun (not Vivian's long center-part hair)
        hair.Ellipsoid(new Vec3(0, 1.66f, -0.01f), new Vec3(0.12f, 0.10f, 0.13f), 18, 12);
        hair.Ellipsoid(new Vec3(0, 1.62f, -0.08f), new Vec3(0.11f, 0.10f, 0.08f), 16, 10);
        hair.Ellipsoid(new Vec3(0, 1.68f, -0.12f), new Vec3(0.07f, 0.07f, 0.07f), 14, 10);

        // Face
        eyeWhite.Ellipsoid(new Vec3(-0.035f, 1.61f, 0.105f), new Vec3(0.022f, 0.016f, 0.012f), 10, 8);
        eyeWhite.Ellipsoid(new Vec3(0.035f, 1.61f, 0.105f), new Vec3(0.022f, 0.016f, 0.012f), 10, 8);
        iris.Ellipsoid(new Vec3(-0.035f, 1.61f, 0.115f), new Vec3(0.012f, 0.012f, 0.006f), 10, 8);
        iris.Ellipsoid(new Vec3(0.035f, 1.61f, 0.115f), new Vec3(0.012f, 0.012f, 0.006f), 10, 8);
        dark.Ellipsoid(new Vec3(-0.035f, 1.61f, 0.120f), new Vec3(0.006f, 0.006f, 0.004f), 8, 6);
        dark.Ellipsoid(new Vec3(0.035f, 1.61f, 0.120f), new Vec3(0.006f, 0.006f, 0.004f), 8, 6);
        dark.Ellipsoid(new Vec3(-0.035f, 1.635f, 0.10f), new Vec3(0.025f, 0.006f, 0.008f), 8, 6);
        dark.Ellipsoid(new Vec3(0.035f, 1.635f, 0.10f), new Vec3(0.025f, 0.006f, 0.008f), 8, 6);
        dark.Ellipsoid(new Vec3(0, 1.505f, 0.108f), new Vec3(0.03f, 0.01f, 0.01f), 10, 6);

        var mats = new Mat[] {
            new Mat("Skin", 0.86f, 0.64f, 0.50f, 0, 0.55f),
            new Mat("Hair", 0.18f, 0.10f, 0.07f, 0, 0.75f),
            new Mat("Sweater", 0.12f, 0.55f, 0.50f, 0, 0.70f),
            new Mat("Pants", 0.12f, 0.18f, 0.30f, 0, 0.80f),
            new Mat("Shoes", 0.08f, 0.08f, 0.09f, 0.1f, 0.55f),
            new Mat("EyeWhite", 0.95f, 0.95f, 0.96f, 0, 0.35f),
            new Mat("Iris", 0.18f, 0.38f, 0.32f, 0, 0.40f),
            new Mat("Dark", 0.12f, 0.07f, 0.06f, 0, 0.50f)
        };
        var meshes = new MeshData[] { skin, hair, sweater, pants, shoes, eyeWhite, iris, dark };
        string[] meshNames = { "Body", "Hair", "Sweater", "Pants", "Shoes", "EyeWhite", "Iris", "BrowsMouth" };

        var bin = new List<byte>();
        var views = new List<string>();
        var accessors = new List<string>();
        var meshJson = new List<string>();

        for (int m = 0; m < meshes.Length; m++)
        {
            MeshData mesh = meshes[m];
            int posOff = Align4(bin.Count);
            while (bin.Count < posOff) bin.Add(0);
            byte[] posBytes = new byte[mesh.Pos.Count * 4];
            Buffer.BlockCopy(mesh.Pos.ToArray(), 0, posBytes, 0, posBytes.Length);
            bin.AddRange(posBytes);

            int norOff = Align4(bin.Count);
            while (bin.Count < norOff) bin.Add(0);
            byte[] norBytes = new byte[mesh.Nor.Count * 4];
            Buffer.BlockCopy(mesh.Nor.ToArray(), 0, norBytes, 0, norBytes.Length);
            bin.AddRange(norBytes);

            int idxOff = Align4(bin.Count);
            while (bin.Count < idxOff) bin.Add(0);
            if (mesh.VertCount > 65535) throw new Exception("Too many verts in " + meshNames[m]);
            byte[] idxBytes = new byte[mesh.Idx.Count * 2];
            for (int i = 0; i < mesh.Idx.Count; i++)
            {
                ushort val = (ushort)mesh.Idx[i];
                idxBytes[i * 2] = (byte)(val & 0xFF);
                idxBytes[i * 2 + 1] = (byte)((val >> 8) & 0xFF);
            }
            bin.AddRange(idxBytes);

            float[] pmin, pmax, nmin, nmax;
            MinMax(mesh.Pos, 3, out pmin, out pmax);
            MinMax(mesh.Nor, 3, out nmin, out nmax);

            int viewPos = views.Count;
            views.Add("{\"buffer\":0,\"byteOffset\":" + posOff + ",\"byteLength\":" + posBytes.Length + ",\"target\":34962}");
            views.Add("{\"buffer\":0,\"byteOffset\":" + norOff + ",\"byteLength\":" + norBytes.Length + ",\"target\":34962}");
            views.Add("{\"buffer\":0,\"byteOffset\":" + idxOff + ",\"byteLength\":" + idxBytes.Length + ",\"target\":34963}");

            int accPos = accessors.Count;
            accessors.Add("{\"bufferView\":" + viewPos + ",\"componentType\":5126,\"count\":" + mesh.VertCount + ",\"type\":\"VEC3\",\"min\":" + Arr(pmin) + ",\"max\":" + Arr(pmax) + "}");
            accessors.Add("{\"bufferView\":" + (viewPos + 1) + ",\"componentType\":5126,\"count\":" + mesh.VertCount + ",\"type\":\"VEC3\",\"min\":" + Arr(nmin) + ",\"max\":" + Arr(nmax) + "}");
            accessors.Add("{\"bufferView\":" + (viewPos + 2) + ",\"componentType\":5123,\"count\":" + mesh.Idx.Count + ",\"type\":\"SCALAR\"}");

            meshJson.Add("{\"name\":\"" + meshNames[m] + "\",\"primitives\":[{\"attributes\":{\"POSITION\":" + accPos + ",\"NORMAL\":" + (accPos + 1) + "},\"indices\":" + (accPos + 2) + ",\"material\":" + m + "}]}");
        }

        while (bin.Count % 4 != 0) bin.Add(0);

        var matJson = new List<string>();
        for (int i = 0; i < mats.Length; i++)
        {
            Mat mat = mats[i];
            matJson.Add("{\"name\":\"" + mat.Name + "\",\"doubleSided\":true,\"pbrMetallicRoughness\":{\"baseColorFactor\":" + Arr(mat.Color) + ",\"metallicFactor\":" + F(mat.Metallic) + ",\"roughnessFactor\":" + F(mat.Roughness) + "}}");
        }

        var nodes = new List<string>();
        nodes.Add("{\"name\":\"Avatar\",\"children\":[1,2,3,4,5,6,7,8]}");
        for (int i = 0; i < meshNames.Length; i++)
            nodes.Add("{\"name\":\"" + meshNames[i] + "\",\"mesh\":" + i + "}");

        string json =
            "{\"asset\":{\"version\":\"2.0\",\"generator\":\"Viviano original avatar builder\"}," +
            "\"scene\":0,\"scenes\":[{\"nodes\":[0]}]," +
            "\"nodes\":[" + string.Join(",", nodes.ToArray()) + "]," +
            "\"meshes\":[" + string.Join(",", meshJson.ToArray()) + "]," +
            "\"materials\":[" + string.Join(",", matJson.ToArray()) + "]," +
            "\"accessors\":[" + string.Join(",", accessors.ToArray()) + "]," +
            "\"bufferViews\":[" + string.Join(",", views.ToArray()) + "]," +
            "\"buffers\":[{\"byteLength\":" + bin.Count + "}]}";

        byte[] jsonBytes = Encoding.UTF8.GetBytes(json);
        int jsonPad = Align4(jsonBytes.Length) - jsonBytes.Length;
        int jsonChunkLen = jsonBytes.Length + jsonPad;
        int binChunkLen = bin.Count;
        int total = 12 + 8 + jsonChunkLen + 8 + binChunkLen;

        using (var fs = new FileStream(path, FileMode.Create, FileAccess.Write))
        using (var bw = new BinaryWriter(fs))
        {
            bw.Write(0x46546C67); // glTF
            bw.Write(2);
            bw.Write(total);
            bw.Write(jsonChunkLen);
            bw.Write(0x4E4F534A); // JSON
            bw.Write(jsonBytes);
            for (int i = 0; i < jsonPad; i++) bw.Write((byte)0x20);
            bw.Write(binChunkLen);
            bw.Write(0x004E4942); // BIN
            bw.Write(bin.ToArray());
        }
    }
}
